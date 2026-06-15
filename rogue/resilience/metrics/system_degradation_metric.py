"""
System degradation metric — measures throughput/correctness loss during faults.
"""

from rogue.resilience.models import MetricResult, ResilienceMetricId, TraceEventType

from .base_resilience_metric import BaseResilienceMetric, MetricEvaluationContext


class SystemDegradationMetric(BaseResilienceMetric):
    """
    Measure system degradation by comparing baseline and fault-window success.

    Computes the ratio of successful agent responses during the fault window
    relative to the baseline task outcome.
    """

    metric_id = ResilienceMetricId.SYSTEM_DEGRADATION

    async def measure(
        self,
        trace,
        context: MetricEvaluationContext,
    ) -> MetricResult:
        """
        Compare baseline and fault-window task success rates.

        Args:
            trace: Experiment trace with baseline and message events.
            context: Evaluation context including architecture profile.

        Returns:
            MetricResult where higher scores mean less degradation.
        """
        profile = context.architecture_profile
        if profile is None or not profile.is_multi_agent():
            return MetricResult(
                metric_id=self.metric_id,
                passed=True,
                score=1.0,
                reason="System degradation not applicable for single-agent runs",
                details={"method": "skipped", "applicable": False},
            )

        baseline_ok = bool(trace.baseline_result and trace.baseline_result.success)
        fault_messages = [
            event
            for event in trace.events
            if event.event_type == TraceEventType.MESSAGE
            and event.payload.get("injected")
        ]
        if not fault_messages:
            return MetricResult(
                metric_id=self.metric_id,
                passed=baseline_ok,
                score=1.0 if baseline_ok else 0.0,
                reason="No fault-window messages recorded",
            )

        successful_fault = sum(
            1
            for event in fault_messages
            if event.payload.get("response") and not event.payload.get("error")
        )
        fault_rate = successful_fault / len(fault_messages)
        baseline_rate = 1.0 if baseline_ok else 0.0

        if baseline_rate == 0.0:
            score = fault_rate
        else:
            score = min(1.0, fault_rate / baseline_rate)

        degradation = max(0.0, 1.0 - score)
        return MetricResult(
            metric_id=self.metric_id,
            passed=degradation <= 0.5,
            score=score,
            value=degradation,
            reason=(
                f"Fault-window success rate {fault_rate:.0%} vs baseline "
                f"{baseline_rate:.0%}"
            ),
            details={
                "method": "heuristic",
                "fault_messages": len(fault_messages),
                "successful_fault": successful_fault,
                "degradation": degradation,
            },
        )
