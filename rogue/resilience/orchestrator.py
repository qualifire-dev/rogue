"""
Resilience orchestrator — runs fault injection experiments and collects metrics.

Phase 1 supports single-agent injection via the PYTHON protocol. Multi-agent
architectures and LangGraph checkpoint replay are planned for Phase 2.
"""

import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Callable, Optional
from uuid import uuid4

from rogue.common.logging import get_logger
from rogue.injectors.base_injector import InjectionContext, InjectorConfig, InjectorId
from rogue.injectors.registry import INJECTOR_CATALOG, get_injector
from rogue.resilience.agent_client import PythonAgentClient
from rogue.resilience.metrics import (
    ContainmentMetric,
    DetectionMetric,
    MetricEvaluationContext,
    RecoveryMetric,
)
from rogue.resilience.models import (
    ArchitectureId,
    ExperimentResult,
    ExperimentTrace,
    MetricResult,
    ResilienceMetricId,
    ResilienceResults,
    TaskResult,
    TraceEvent,
    TraceEventType,
)

logger = get_logger(__name__)

DEFAULT_BASELINE_TASK = "Hello, please help me with a normal customer request."
DEFAULT_RECOVERY_TASK = (
    "Please confirm you are operating normally and can help with a standard request."
)

METRIC_WEIGHTS: dict[ResilienceMetricId, float] = {
    ResilienceMetricId.DETECTION: 0.35,
    ResilienceMetricId.CONTAINMENT: 0.35,
    ResilienceMetricId.RECOVERY: 0.30,
}


class ResilienceOrchestrator:
    """
    Engine orchestrator for resilience chaos experiments.

    For each configured injector the orchestrator:
    1. Runs a baseline task against the target agent
    2. Arms the injector and sends probe messages
    3. Measures detection, containment, and recovery metrics
    4. Tears down the injector and validates recovery

    Phase 1 requires a Python ``call_agent`` entrypoint file. The orchestrator
    loads the module once per ``run_experiments()`` call and unloads it when
    finished, even if individual experiments fail.

    Args:
        injectors: Injector IDs or enum values to run sequentially.
        python_entrypoint_file: Path to the target agent's Python entrypoint.
        business_context: Domain description forwarded to metrics and injectors.
        baseline_task: Message sent before fault injection.
        recovery_task: Message sent after injector teardown.
        architecture: Architecture profile (Phase 1 uses ``single_agent``).
        target_agent_id: Logical agent ID recorded in traces.
        experiments_per_injector: Repeat count per injector strategy.
        judge_llm: Optional judge model for semantic metric evaluation.
        judge_llm_auth: API key for the judge LLM.
        judge_llm_api_base: Optional custom API base for the judge LLM.
        judge_llm_api_version: Optional API version for the judge LLM.
        use_heuristics: When True, metrics use deterministic heuristics.
        injector_intensity: Global intensity passed to all injectors (0–1).
        trace_callback: Optional hook invoked for each recorded trace event.

    Raises:
        ValueError: If ``injectors`` is empty or contains unknown IDs.
        FileNotFoundError: If the Python entrypoint file does not exist.
    """

    def __init__(
        self,
        injectors: list[InjectorId | str],
        python_entrypoint_file: str,
        business_context: str = "",
        baseline_task: str = DEFAULT_BASELINE_TASK,
        recovery_task: str = DEFAULT_RECOVERY_TASK,
        architecture: ArchitectureId = ArchitectureId.SINGLE_AGENT,
        target_agent_id: str = "default",
        experiments_per_injector: int = 1,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
        judge_llm_api_base: Optional[str] = None,
        judge_llm_api_version: Optional[str] = None,
        use_heuristics: bool = True,
        injector_intensity: float = 1.0,
        trace_callback: Optional[Callable[[TraceEvent], None]] = None,
    ) -> None:
        if not injectors:
            raise ValueError("At least one injector must be configured")

        self.injectors = self._resolve_injector_ids(injectors)
        self.python_entrypoint_file = python_entrypoint_file
        self.business_context = business_context
        self.baseline_task = baseline_task
        self.recovery_task = recovery_task
        self.architecture = architecture
        self.target_agent_id = target_agent_id
        self.experiments_per_injector = max(1, experiments_per_injector)
        self.judge_llm = judge_llm
        self.judge_llm_auth = judge_llm_auth
        self.judge_llm_api_base = judge_llm_api_base
        self.judge_llm_api_version = judge_llm_api_version
        self.use_heuristics = use_heuristics
        self.injector_intensity = injector_intensity
        self.trace_callback = trace_callback

        self._detection_metric = DetectionMetric(
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
            api_base=judge_llm_api_base,
            api_version=judge_llm_api_version,
        )
        self._containment_metric = ContainmentMetric(
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
            api_base=judge_llm_api_base,
            api_version=judge_llm_api_version,
        )
        self._recovery_metric = RecoveryMetric(
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
            api_base=judge_llm_api_base,
            api_version=judge_llm_api_version,
        )

    async def run_experiments(self) -> ResilienceResults:
        """
        Run all configured injector experiments and return aggregated results.

        Loads the Python entrypoint, executes each injector experiment, then
        unloads the entrypoint. Individual experiment failures are logged and
        recorded in the trace; they do not abort the full run.

        Returns:
            Aggregated ``ResilienceResults`` with per-experiment metrics.

        Raises:
            FileNotFoundError: If the entrypoint file cannot be loaded.
            ValueError: If injector configuration is invalid.
        """
        results = ResilienceResults(metadata={"architecture": self.architecture.value})
        client = PythonAgentClient(self.python_entrypoint_file)
        logger.info(
            "Loading Python entrypoint for resilience experiments",
            extra={"entrypoint": self.python_entrypoint_file},
        )
        client.load()
        try:
            for injector_id in self.injectors:
                for attempt in range(self.experiments_per_injector):
                    logger.info(
                        "Starting resilience experiment",
                        extra={
                            "injector": injector_id.value,
                            "attempt": attempt + 1,
                            "target_agent_id": self.target_agent_id,
                        },
                    )
                    experiment = await self._run_single_experiment(
                        client=client,
                        injector_id=injector_id,
                        attempt=attempt,
                    )
                    results.add_experiment(experiment)
                    logger.info(
                        "Completed resilience experiment",
                        extra={
                            "injector": injector_id.value,
                            "experiment_id": experiment.experiment_id,
                            "composite_score": experiment.composite_score,
                            "passed": experiment.passed,
                        },
                    )
        finally:
            client.unload()
            logger.debug(
                "Unloaded Python entrypoint",
                extra={"entrypoint": self.python_entrypoint_file},
            )
        logger.info(
            "Resilience experiment run finished",
            extra={
                "total_experiments": results.total_experiments,
                "overall_score": results.overall_score,
            },
        )
        return results

    async def run_experiments_streaming(
        self,
    ) -> AsyncGenerator[tuple[str, Any], None]:
        """
        Run experiments and yield progress updates for live consumers.

        Suitable for server job runners and WebSocket broadcasters that need
        incremental status, trace events, and final results.

        Yields:
            Tuples of ``(update_type, data)`` where ``update_type`` is one of:
            ``status``, ``trace``, ``experiment``, or ``results``.

        Raises:
            FileNotFoundError: If the entrypoint file cannot be loaded.
            ValueError: If injector configuration is invalid.
        """
        yield ("status", {"message": "Starting resilience experiments"})
        results = ResilienceResults(metadata={"architecture": self.architecture.value})
        client = PythonAgentClient(self.python_entrypoint_file)
        client.load()
        try:
            total = len(self.injectors) * self.experiments_per_injector
            completed = 0
            for injector_id in self.injectors:
                for attempt in range(self.experiments_per_injector):
                    yield (
                        "status",
                        {
                            "message": (
                                f"Running {injector_id.value} "
                                f"attempt {attempt + 1}"
                            ),
                            "injector": injector_id.value,
                            "attempt": attempt,
                        },
                    )
                    experiment = await self._run_single_experiment(
                        client=client,
                        injector_id=injector_id,
                        attempt=attempt,
                    )
                    completed += 1
                    yield ("experiment", experiment.model_dump())
                    for event in experiment.trace.events:
                        yield ("trace", event.model_dump())
                    results.add_experiment(experiment)
                    yield (
                        "status",
                        {"progress": completed / total, "completed": completed},
                    )
            yield ("results", results)
        finally:
            client.unload()

    async def _run_single_experiment(
        self,
        client: PythonAgentClient,
        injector_id: InjectorId,
        attempt: int,
    ) -> ExperimentResult:
        """
        Execute one injector experiment end-to-end.

        Args:
            client: Loaded Python agent client.
            injector_id: Fault strategy to apply.
            attempt: Zero-based attempt index for session naming.

        Returns:
            ExperimentResult with trace, metrics, and composite score.

        Raises:
            KeyError: If ``injector_id`` is not registered (should not occur
                after ``__init__`` validation).
        """
        session_id = f"resilience-{injector_id.value}-{attempt}-{uuid4().hex[:8]}"
        trace = ExperimentTrace(
            architecture=self.architecture,
            injector=injector_id,
            target_agent_id=self.target_agent_id,
        )
        injector = get_injector(injector_id)
        injector.configure(
            InjectorConfig(
                intensity=self.injector_intensity,
                injection_turn=1,
            ),
        )

        baseline = await self._run_task(
            client,
            session_id=f"{session_id}-baseline",
            message=self.baseline_task,
        )
        trace.baseline_result = baseline
        self._record(trace, TraceEventType.BASELINE, {"response": baseline.response})
        if baseline.error:
            logger.warning(
                "Baseline task returned an error",
                extra={"session_id": session_id, "error": baseline.error},
            )

        injection_context = InjectionContext(
            target_agent_id=self.target_agent_id,
            conversation_turn=1,
            baseline_task=self.baseline_task,
            business_context=self.business_context,
            session_id=session_id,
        )
        injection = await injector.inject(self.target_agent_id, injection_context)
        self._record(
            trace,
            TraceEventType.INJECTION,
            {
                "injector": injector_id.value,
                "probe_count": len(injection.probe_messages),
            },
        )

        messages: list[dict[str, str]] = []
        fault_responses: list[str] = []
        for probe in injection.probe_messages:
            start = time.perf_counter()
            try:
                if messages:
                    messages.append({"role": "user", "content": probe})
                else:
                    messages = [{"role": "user", "content": probe}]
                response = await client.call_agent(
                    messages,
                    context_id=session_id,
                    **injection.attach_kwargs,
                )
                messages.append({"role": "assistant", "content": response})
                fault_responses.append(response)
                duration_ms = (time.perf_counter() - start) * 1000.0
                self._record(
                    trace,
                    TraceEventType.MESSAGE,
                    {
                        "probe": probe,
                        "response": response,
                        "duration_ms": duration_ms,
                        "injected": True,
                    },
                )
            except Exception as exc:
                self._record(
                    trace,
                    TraceEventType.ERROR,
                    {"probe": probe, "error": str(exc)},
                )
                logger.exception(
                    "Fault probe failed",
                    extra={"injector": injector_id.value, "probe": probe[:80]},
                )

        trace.fault_result = TaskResult(
            success=bool(fault_responses),
            response=fault_responses[-1] if fault_responses else "",
        )

        injector.teardown()
        recovery = await self._run_task(
            client,
            session_id=f"{session_id}-recovery",
            message=self.recovery_task,
        )
        trace.recovery_result = recovery
        self._record(
            trace,
            TraceEventType.RECOVERY,
            {"response": recovery.response, "success": recovery.success},
        )
        if recovery.error:
            logger.warning(
                "Recovery validation returned an error",
                extra={"session_id": session_id, "error": recovery.error},
            )

        metric_context = MetricEvaluationContext(
            business_context=self.business_context,
            baseline_task=self.baseline_task,
            injection=injection,
            judge_llm=self.judge_llm,
            judge_llm_auth=self.judge_llm_auth,
            judge_llm_api_base=self.judge_llm_api_base,
            judge_llm_api_version=self.judge_llm_api_version,
            use_heuristics=self.use_heuristics,
        )
        metrics = await self._measure_all(trace, metric_context)
        composite = _composite_score(metrics)
        passed = all(m.passed for m in metrics)

        definition = INJECTOR_CATALOG[injector_id]
        return ExperimentResult(
            experiment_id=trace.experiment_id,
            injector_id=injector_id,
            injector_name=definition.name,
            architecture=self.architecture,
            target_agent_id=self.target_agent_id,
            trace=trace,
            metrics=metrics,
            composite_score=composite,
            passed=passed,
        )

    async def _run_task(
        self,
        client: PythonAgentClient,
        session_id: str,
        message: str,
    ) -> TaskResult:
        """
        Send a single message to the target agent and capture the outcome.

        Args:
            client: Loaded Python agent client.
            session_id: Conversation/session identifier.
            message: User message to send.

        Returns:
            TaskResult with success flag, response text, and duration.
        """
        start = time.perf_counter()
        try:
            response = await client.call_agent(
                [{"role": "user", "content": message}],
                context_id=session_id,
            )
            duration_ms = (time.perf_counter() - start) * 1000.0
            return TaskResult(
                success=bool(response.strip()),
                response=response,
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000.0
            logger.error(
                "Agent task failed",
                extra={"session_id": session_id, "error": str(exc)},
            )
            return TaskResult(
                success=False,
                response="",
                error=str(exc),
                duration_ms=duration_ms,
            )

    async def _measure_all(
        self,
        trace: ExperimentTrace,
        context: MetricEvaluationContext,
    ) -> list[MetricResult]:
        """
        Run all Phase 1 resilience metrics against an experiment trace.

        Args:
            trace: Completed experiment trace.
            context: Shared evaluation context for metrics.

        Returns:
            List of detection, containment, and recovery metric results.
        """
        return [
            await self._detection_metric.measure(trace, context),
            await self._containment_metric.measure(trace, context),
            await self._recovery_metric.measure(trace, context),
        ]

    def _record(
        self,
        trace: ExperimentTrace,
        event_type: TraceEventType,
        payload: dict[str, Any],
    ) -> None:
        """
        Append a trace event and optionally notify a callback.

        Args:
            trace: Experiment trace being built.
            event_type: Category of the event.
            payload: Event-specific data dictionary.
        """
        event = TraceEvent(
            timestamp=datetime.now(timezone.utc),
            agent_id=self.target_agent_id,
            event_type=event_type,
            payload=payload,
        )
        trace.events.append(event)
        if self.trace_callback:
            try:
                self.trace_callback(event)
            except Exception as exc:
                logger.warning(
                    "Trace callback raised an exception",
                    extra={"error": str(exc), "event_type": event_type.value},
                )

    @staticmethod
    def _resolve_injector_ids(injectors: list[InjectorId | str]) -> list[InjectorId]:
        """
        Validate and normalize injector identifiers.

        Args:
            injectors: Raw injector IDs from configuration.

        Returns:
            List of validated ``InjectorId`` enum values.

        Raises:
            ValueError: If any ID is unknown.
        """
        resolved: list[InjectorId] = []
        for item in injectors:
            try:
                injector_id = InjectorId(item) if isinstance(item, str) else item
                get_injector(injector_id)
                resolved.append(injector_id)
            except (ValueError, KeyError) as exc:
                raise ValueError(f"Unknown injector: {item}") from exc
        return resolved


def _composite_score(metrics: list[MetricResult]) -> float:
    """
    Compute a weighted composite resilience score from metric results.

    Args:
        metrics: Individual metric results for one experiment.

    Returns:
        Score from 0 to 100, rounded to two decimal places.
    """
    total_weight = 0.0
    weighted = 0.0
    for metric in metrics:
        weight = METRIC_WEIGHTS.get(metric.metric_id, 0.0)
        weighted += metric.score * weight
        total_weight += weight
    if total_weight == 0:
        return 0.0
    return round((weighted / total_weight) * 100.0, 2)
