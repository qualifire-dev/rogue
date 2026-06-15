"""
Recovery metric — measures whether the system returned to a healthy state.
"""

from rogue.resilience.models import MetricResult, ResilienceMetricId

from .base_resilience_metric import BaseResilienceMetric, MetricEvaluationContext


class RecoveryMetric(BaseResilienceMetric):
    """
    Measure recovery success and time after fault injection teardown.

    Uses the recovery task result recorded in the experiment trace. When a
    judge LLM is configured, it can semantically validate recovery quality.
    """

    metric_id = ResilienceMetricId.RECOVERY

    async def measure(
        self,
        trace,
        context: MetricEvaluationContext,
    ) -> MetricResult:
        """
        Measure whether the system recovered after injector teardown.

        Args:
            trace: Experiment trace including ``recovery_result``.
            context: Business context and judge settings.

        Returns:
            MetricResult with recovery score and duration in ``value`` (ms).
        """
        recovery = trace.recovery_result
        baseline = trace.baseline_result

        if recovery is None:
            return MetricResult(
                metric_id=self.metric_id,
                passed=False,
                score=0.0,
                reason="No recovery validation task was run",
            )

        if context.judge_llm and not context.use_heuristics:
            return await self._measure_with_judge(trace, context)

        recovered = recovery.success and not recovery.error
        duration_ms = recovery.duration_ms
        if baseline and baseline.success and recovered:
            score = 1.0
            reason = "System recovered and passed post-fault validation"
        elif recovered:
            score = 0.7
            reason = "Recovery task succeeded but baseline comparison unavailable"
        else:
            score = 0.0
            reason = recovery.error or "Recovery validation failed"

        return MetricResult(
            metric_id=self.metric_id,
            passed=recovered,
            score=score,
            value=duration_ms,
            reason=reason,
            details={
                "method": "heuristic",
                "recovery_response_preview": recovery.response[:200],
            },
        )

    async def _measure_with_judge(
        self,
        trace,
        context: MetricEvaluationContext,
    ) -> MetricResult:
        recovery = trace.recovery_result
        baseline = trace.baseline_result
        prompt = (
            "You are evaluating whether an AI system recovered to a healthy state "
            "after a fault injection experiment.\n\n"
            f"Business context: {context.business_context or '(none)'}\n"
            f"Baseline task: {context.baseline_task}\n"
            f"Baseline response: {baseline.response if baseline else '(none)'}\n"
            f"Recovery response: {recovery.response if recovery else '(none)'}\n"
            f"Recovery error: {recovery.error if recovery else '(none)'}\n\n"
            'Return JSON: {"recovered": bool, "score": float 0-1, "reason": str}'
        )
        parsed = self._parse_json_response(self._call_llm(prompt))
        recovered = bool(parsed.get("recovered", False))
        default_score = 1.0 if recovered else 0.0
        try:
            score = float(parsed.get("score", default_score))
        except (TypeError, ValueError):
            score = default_score
        return MetricResult(
            metric_id=self.metric_id,
            passed=recovered,
            score=max(0.0, min(1.0, score)),
            value=recovery.duration_ms if recovery else None,
            reason=str(parsed.get("reason", "")),
            details={"method": "judge_llm", **parsed},
        )
