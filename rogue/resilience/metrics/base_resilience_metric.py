"""
Base resilience metric class.

Metrics evaluate detection, containment, and recovery behavior from
experiment traces produced by the resilience orchestrator.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Optional

from loguru import logger
from pydantic import BaseModel, Field

from rogue.common.agent_model_wrapper import get_llm_from_model
from rogue.injectors.base_injector import InjectionResult
from rogue.resilience.models import ExperimentTrace, MetricResult, ResilienceMetricId


class MetricEvaluationContext(BaseModel):
    """Shared context passed to each metric during evaluation."""

    business_context: str = ""
    baseline_task: str = ""
    injection: Optional[InjectionResult] = None
    architecture_profile: Optional[Any] = Field(
        default=None,
        description="ArchitectureProfile when running multi-agent experiments",
    )
    judge_llm: Optional[str] = None
    judge_llm_auth: Optional[str] = None
    judge_llm_api_base: Optional[str] = None
    judge_llm_api_version: Optional[str] = None
    use_heuristics: bool = Field(
        default=True,
        description=(
            "When True and no judge LLM is configured, metrics fall back to "
            "deterministic heuristics suitable for tests and offline runs."
        ),
    )


class BaseResilienceMetric(ABC):
    """
    Base class for resilience evaluation metrics.

    Subclasses measure one aspect of system behavior during a fault
    injection experiment: detection, containment, or recovery.
    """

    metric_id: ResilienceMetricId

    def __init__(
        self,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> None:
        """
        Initialize the metric with optional judge LLM settings.

        Args:
            judge_llm: Model name for semantic evaluation (optional).
            judge_llm_auth: API key for the judge LLM.
            api_base: Optional custom API base URL.
            api_version: Optional API version string.
        """
        self.judge_llm = judge_llm
        self.judge_llm_auth = judge_llm_auth
        self.api_base = api_base
        self.api_version = api_version
        self._llm_instance: Any = None

    def _get_llm(self) -> Any:
        if self._llm_instance:
            return self._llm_instance
        if not self.judge_llm:
            return None
        try:
            self._llm_instance = get_llm_from_model(
                self.judge_llm,
                self.judge_llm_auth,
                api_base=self.api_base,
                api_version=self.api_version,
            )
            return self._llm_instance
        except Exception as exc:
            logger.error(f"Failed to initialize judge LLM {self.judge_llm}: {exc}")
            return None

    def _call_llm(self, prompt: str) -> str:
        llm = self._get_llm()
        if not llm:
            return ""
        try:
            llm_type = type(llm).__name__
            if llm_type == "LiteLlm":
                from litellm import completion

                response = completion(
                    model=getattr(llm, "model", self.judge_llm),
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": "evaluate"},
                    ],
                    api_key=getattr(llm, "api_key", self.judge_llm_auth),
                    api_base=self.api_base,
                    api_version=self.api_version,
                )
                return response.choices[0].message.content or ""
            if hasattr(llm, "query"):
                return llm.query(prompt)
            if hasattr(llm, "generate_content"):
                resp = llm.generate_content(prompt)
                return resp.text if hasattr(resp, "text") else str(resp)
        except Exception as exc:
            logger.error(f"Error calling judge LLM: {exc}")
        return ""

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        if not response or not response.strip():
            return {}
        clean = response.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        try:
            parsed = json.loads(clean.strip())
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    @abstractmethod
    async def measure(
        self,
        trace: ExperimentTrace,
        context: MetricEvaluationContext,
    ) -> MetricResult:
        """
        Measure this metric from an experiment trace.

        Args:
            trace: Completed experiment trace produced by the orchestrator.
            context: Shared evaluation context including injection metadata.

        Returns:
            Normalized metric result with score between 0 and 1.
        """
