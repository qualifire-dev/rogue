"""
Resilience report generator — markdown, CSV, and structured dashboard data.

Maps ``ResilienceResults`` from the orchestrator into scorecards, timelines,
agent graphs, and exportable artifacts for the web UI and CLI.
"""

import csv
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from rogue.common.logging import get_logger
from rogue.injectors.registry import INJECTOR_CATALOG, InjectorId
from rogue.resilience.catalog.architectures import get_architecture
from rogue.resilience.models import (
    ArchitectureId,
    ExperimentResult,
    ResilienceMetricId,
    ResilienceResults,
    TraceEventType,
)

from .models import (
    ResilienceReport,
    ResilienceReportAgentEdge,
    ResilienceReportAgentGraph,
    ResilienceReportAgentNode,
    ResilienceReportCheckpointStep,
    ResilienceReportExperimentRow,
    ResilienceReportHighlights,
    ResilienceReportKeyFinding,
    ResilienceReportMetadata,
    ResilienceReportMetricRadar,
    ResilienceReportTimelineEvent,
)

logger = get_logger(__name__)

_EVENT_LABELS: dict[str, str] = {
    TraceEventType.BASELINE.value: "Baseline",
    TraceEventType.INJECTION.value: "Fault injection",
    TraceEventType.MESSAGE.value: "Probe message",
    TraceEventType.DETECTION.value: "Detection",
    TraceEventType.CONTAINMENT.value: "Containment",
    TraceEventType.RECOVERY.value: "Recovery",
    TraceEventType.CHECKPOINT.value: "Checkpoint",
    TraceEventType.ERROR.value: "Error",
    TraceEventType.TOOL_CALL.value: "Tool call",
}


class ResilienceReportGenerator:
    """
    Generate resilience reports from orchestrator results.

    Produces structured data for the dashboard, plus markdown and CSV exports
    suitable for CI artifacts and CLI output.
    """

    def __init__(
        self,
        results: ResilienceResults,
        *,
        architecture: str = "single_agent",
        target_agent_id: str = "default",
        injectors: Optional[list[str]] = None,
        experiments_per_injector: int = 1,
        use_heuristics: bool = True,
        enable_checkpoint_recovery: bool = False,
        judge_llm: Optional[str] = None,
        export_dir: Optional[Path] = None,
    ) -> None:
        self.results = results
        self.architecture = architecture
        self.target_agent_id = target_agent_id
        self.injectors = injectors or []
        self.experiments_per_injector = experiments_per_injector
        self.use_heuristics = use_heuristics
        self.enable_checkpoint_recovery = enable_checkpoint_recovery
        self.judge_llm = judge_llm
        self.export_dir = export_dir

    @classmethod
    def from_results_dict(
        cls,
        results_data: dict[str, Any],
        **kwargs: Any,
    ) -> "ResilienceReportGenerator":
        """Build a generator from serialized job results."""
        results = ResilienceResults.model_validate(results_data)
        metadata = results_data.get("metadata") or {}
        return cls(
            results=results,
            architecture=str(metadata.get("architecture", kwargs.get("architecture", "single_agent"))),
            target_agent_id=str(
                metadata.get("target_agent_id", kwargs.get("target_agent_id", "default")),
            ),
            **{k: v for k, v in kwargs.items() if k not in ("architecture", "target_agent_id")},
        )

    def generate_full_report(self) -> ResilienceReport:
        """Build the complete report with exports."""
        profile = self._resolve_architecture()
        is_multi = profile.is_multi_agent()
        metadata = ResilienceReportMetadata(
            experiment_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            architecture=self.architecture,
            architecture_name=profile.name,
            target_agent_id=self.target_agent_id,
            injectors=self.injectors,
            experiments_per_injector=self.experiments_per_injector,
            use_heuristics=self.use_heuristics,
            enable_checkpoint_recovery=self.enable_checkpoint_recovery,
            judge_llm=self.judge_llm,
        )
        highlights = ResilienceReportHighlights(
            overall_score=self.results.overall_score,
            total_experiments=self.results.total_experiments,
            experiments_passed=self.results.experiments_passed,
            detection_rate=self.results.detection_rate,
            containment_rate=self.results.containment_rate,
            recovery_rate=self.results.recovery_rate,
            cascading_failure_rate=self.results.cascading_failure_rate,
            system_degradation_rate=self.results.system_degradation_rate,
            is_multi_agent=is_multi,
        )
        experiment_table = [self._experiment_row(exp) for exp in self.results.experiments]
        metrics_radar = ResilienceReportMetricRadar(
            detection=self.results.detection_rate,
            containment=self.results.containment_rate,
            recovery=self.results.recovery_rate,
            cascading_failure=(
                self.results.cascading_failure_rate if is_multi else None
            ),
            system_degradation=(
                self.results.system_degradation_rate if is_multi else None
            ),
        )
        timeline = self._build_timeline()
        agent_graph = self._build_agent_graph(profile)
        checkpoint_steps = self._build_checkpoint_steps()
        key_findings = self._build_key_findings()
        markdown = self._generate_markdown(
            metadata,
            highlights,
            experiment_table,
            key_findings,
        )
        csv_path = self._write_csv_summary(experiment_table)

        return ResilienceReport(
            metadata=metadata,
            highlights=highlights,
            experiment_table=experiment_table,
            metrics_radar=metrics_radar,
            timeline=timeline,
            agent_graph=agent_graph,
            checkpoint_steps=checkpoint_steps,
            key_findings=key_findings,
            markdown_report=markdown,
            csv_summary_path=str(csv_path) if csv_path else None,
        )

    def _resolve_architecture(self) -> Any:
        try:
            return get_architecture(ArchitectureId(self.architecture))
        except ValueError:
            logger.warning(
                "Unknown architecture in report; using single_agent",
                extra={"architecture": self.architecture},
            )
            return get_architecture(ArchitectureId.SINGLE_AGENT)

    def _metric_score(
        self,
        experiment: ExperimentResult,
        metric_id: ResilienceMetricId,
    ) -> float:
        for metric in experiment.metrics:
            if metric.metric_id == metric_id:
                return metric.score
        return 0.0

    def _experiment_row(self, experiment: ExperimentResult) -> ResilienceReportExperimentRow:
        injector_name = experiment.injector_name
        if not injector_name:
            try:
                inj_id = InjectorId(experiment.injector_id)
                injector_name = INJECTOR_CATALOG[inj_id].name
            except (ValueError, KeyError):
                injector_name = str(experiment.injector_id)

        row = ResilienceReportExperimentRow(
            experiment_id=experiment.experiment_id,
            injector_id=str(experiment.injector_id),
            injector_name=injector_name,
            architecture=str(experiment.architecture),
            target_agent_id=experiment.target_agent_id,
            composite_score=experiment.composite_score,
            passed=experiment.passed,
            detection_score=self._metric_score(experiment, ResilienceMetricId.DETECTION),
            containment_score=self._metric_score(experiment, ResilienceMetricId.CONTAINMENT),
            recovery_score=self._metric_score(experiment, ResilienceMetricId.RECOVERY),
        )
        cascade = self._metric_score(experiment, ResilienceMetricId.CASCADING_FAILURE)
        degradation = self._metric_score(experiment, ResilienceMetricId.SYSTEM_DEGRADATION)
        if any(
            m.metric_id == ResilienceMetricId.CASCADING_FAILURE for m in experiment.metrics
        ):
            row.cascading_score = cascade
            row.degradation_score = degradation
        return row

    def _build_timeline(self) -> list[ResilienceReportTimelineEvent]:
        events: list[ResilienceReportTimelineEvent] = []
        for experiment in self.results.experiments:
            injector_id = str(experiment.injector_id)
            for event in experiment.trace.events:
                event_type = (
                    event.event_type.value
                    if hasattr(event.event_type, "value")
                    else str(event.event_type)
                )
                label = _EVENT_LABELS.get(event_type, event_type.replace("_", " ").title())
                ts = event.timestamp
                if hasattr(ts, "isoformat"):
                    ts_str = ts.isoformat()
                else:
                    ts_str = str(ts)
                events.append(
                    ResilienceReportTimelineEvent(
                        timestamp=ts_str,
                        experiment_id=experiment.experiment_id,
                        injector_id=injector_id,
                        agent_id=event.agent_id,
                        event_type=event_type,
                        label=label,
                        payload=event.payload,
                    ),
                )
        events.sort(key=lambda e: e.timestamp)
        return events

    def _build_agent_graph(self, profile: Any) -> ResilienceReportAgentGraph:
        nodes = [
            ResilienceReportAgentNode(
                agent_id=agent.agent_id,
                role=agent.role,
                is_target=agent.agent_id == self.target_agent_id,
                is_rogue=agent.agent_id == self.target_agent_id,
            )
            for agent in profile.agents
        ]
        edges: list[ResilienceReportAgentEdge] = []
        for source, targets in profile.notify_on_fault.items():
            for target in targets:
                edges.append(
                    ResilienceReportAgentEdge(
                        source=source,
                        target=target,
                        label="notify on fault",
                    ),
                )
        if profile.is_multi_agent() and profile.entry_agent_id:
            for agent in profile.agents:
                if agent.agent_id != profile.entry_agent_id and agent.role == "worker":
                    edges.append(
                        ResilienceReportAgentEdge(
                            source=profile.entry_agent_id,
                            target=agent.agent_id,
                            label="delegates",
                        ),
                    )
        return ResilienceReportAgentGraph(nodes=nodes, edges=edges)

    def _build_checkpoint_steps(self) -> list[ResilienceReportCheckpointStep]:
        steps: list[ResilienceReportCheckpointStep] = []
        for experiment in self.results.experiments:
            for event in experiment.trace.events:
                event_type = (
                    event.event_type.value
                    if hasattr(event.event_type, "value")
                    else str(event.event_type)
                )
                if event_type != TraceEventType.CHECKPOINT.value:
                    continue
                payload = event.payload
                ts = event.timestamp
                ts_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
                steps.append(
                    ResilienceReportCheckpointStep(
                        timestamp=ts_str,
                        experiment_id=experiment.experiment_id,
                        operation=str(payload.get("operation", "checkpoint")),
                        success=bool(payload.get("success", False)),
                        thread_id=payload.get("thread_id"),
                        checkpoint_id=payload.get("checkpoint_id"),
                        error=payload.get("error"),
                    ),
                )
        steps.sort(key=lambda s: s.timestamp)
        return steps

    def _build_key_findings(self) -> list[ResilienceReportKeyFinding]:
        sorted_experiments = sorted(
            self.results.experiments,
            key=lambda e: e.composite_score,
        )
        findings: list[ResilienceReportKeyFinding] = []
        for experiment in sorted_experiments[:5]:
            if experiment.passed and experiment.composite_score >= 80:
                continue
            failed = [
                m.metric_id.value
                for m in experiment.metrics
                if not m.passed
            ]
            findings.append(
                ResilienceReportKeyFinding(
                    injector_id=str(experiment.injector_id),
                    injector_name=experiment.injector_name,
                    composite_score=experiment.composite_score,
                    summary=self._finding_summary(experiment, failed),
                    failed_metrics=failed,
                ),
            )
        return findings[:3]

    def _finding_summary(
        self,
        experiment: ExperimentResult,
        failed_metrics: list[str],
    ) -> str:
        if not failed_metrics:
            return (
                f"{experiment.injector_name} scored {experiment.composite_score:.0f}/100 "
                f"— review trace for improvement opportunities."
            )
        metrics_str = ", ".join(m.replace("_", " ") for m in failed_metrics)
        return (
            f"{experiment.injector_name} failed {metrics_str} "
            f"(score {experiment.composite_score:.0f}/100)."
        )

    def _generate_markdown(
        self,
        metadata: ResilienceReportMetadata,
        highlights: ResilienceReportHighlights,
        experiment_table: list[ResilienceReportExperimentRow],
        key_findings: list[ResilienceReportKeyFinding],
    ) -> str:
        lines = [
            "# Rogue Resilience Report",
            "",
            f"**Date:** {metadata.experiment_date}",
            f"**Architecture:** {metadata.architecture_name} (`{metadata.architecture}`)",
            f"**Target agent:** `{metadata.target_agent_id}`",
            f"**Injectors:** {', '.join(metadata.injectors) or '—'}",
            "",
            "## Scorecard",
            "",
            f"- **Overall score:** {highlights.overall_score:.1f}/100",
            f"- **Experiments passed:** {highlights.experiments_passed}/{highlights.total_experiments}",
            f"- **Detection rate:** {highlights.detection_rate:.0%}",
            f"- **Containment rate:** {highlights.containment_rate:.0%}",
            f"- **Recovery rate:** {highlights.recovery_rate:.0%}",
        ]
        if highlights.is_multi_agent:
            lines.extend(
                [
                    f"- **Cascade resilience:** {highlights.cascading_failure_rate:.0%}",
                    f"- **System degradation:** {highlights.system_degradation_rate:.0%}",
                ],
            )
        if key_findings:
            lines.extend(["", "## Key findings", ""])
            for finding in key_findings:
                lines.append(f"- **{finding.injector_name}** — {finding.summary}")
        if experiment_table:
            lines.extend(
                [
                    "",
                    "## Per-injector results",
                    "",
                    "| Injector | Score | Passed | Detection | Containment | Recovery |",
                    "| --- | ---: | :---: | ---: | ---: | ---: |",
                ],
            )
            for row in experiment_table:
                lines.append(
                    f"| {row.injector_name} | {row.composite_score:.0f} | "
                    f"{'✓' if row.passed else '✗'} | "
                    f"{row.detection_score:.0%} | {row.containment_score:.0%} | "
                    f"{row.recovery_score:.0%} |",
                )
        return "\n".join(lines)

    def generate_csv_summary(self) -> str:
        """Return CSV summary as a string."""
        rows = [self._experiment_row(exp) for exp in self.results.experiments]
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "experiment_id",
                "injector_id",
                "injector_name",
                "architecture",
                "target_agent_id",
                "composite_score",
                "passed",
                "detection_score",
                "containment_score",
                "recovery_score",
                "cascading_score",
                "degradation_score",
            ],
        )
        for row in rows:
            writer.writerow(
                [
                    row.experiment_id,
                    row.injector_id,
                    row.injector_name,
                    row.architecture,
                    row.target_agent_id,
                    f"{row.composite_score:.2f}",
                    row.passed,
                    f"{row.detection_score:.4f}",
                    f"{row.containment_score:.4f}",
                    f"{row.recovery_score:.4f}",
                    f"{row.cascading_score:.4f}" if row.cascading_score is not None else "",
                    f"{row.degradation_score:.4f}" if row.degradation_score is not None else "",
                ],
            )
        return buffer.getvalue()

    def _write_csv_summary(
        self,
        experiment_table: list[ResilienceReportExperimentRow],
    ) -> Optional[Path]:
        if not self.export_dir:
            return None
        try:
            self.export_dir.mkdir(parents=True, exist_ok=True)
            path = self.export_dir / "resilience_summary.csv"
            path.write_text(self.generate_csv_summary(), encoding="utf-8")
            return path
        except OSError as exc:
            logger.warning(
                "Failed to write resilience CSV export",
                extra={"error": str(exc)},
            )
            return None
