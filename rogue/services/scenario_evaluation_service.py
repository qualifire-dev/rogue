from typing import AsyncGenerator, Any

from loguru import logger

from ..evaluator_agent.run_evaluator_agent import arun_evaluator_agent
from ..models.config import AuthType
from ..models.evaluation_result import (
    EvaluationResults,
)
from ..models.scenario import Scenarios


class ScenarioEvaluationService:
    def __init__(
        self,
        evaluated_agent_url: str,
        evaluated_agent_auth_type: AuthType,
        evaluated_agent_auth_credentials: str | None,
        judge_llm: str,
        judge_llm_api_key: str | None,
        scenarios: Scenarios,
        business_context: str,
        deep_test_mode: bool,
    ):
        self._evaluated_agent_url = evaluated_agent_url
        self._evaluated_agent_auth_type = evaluated_agent_auth_type
        self._evaluated_agent_auth_credentials = evaluated_agent_auth_credentials
        self._judge_llm = judge_llm
        self._judge_llm_api_key = judge_llm_api_key
        self._scenarios = scenarios
        self._business_context = business_context
        self._deep_test_mode = deep_test_mode
        self._results = EvaluationResults()

    async def evaluate_scenarios(self) -> AsyncGenerator[tuple[str, Any], None]:
        if not self._scenarios.scenarios:
            yield "status", "No scenarios to evaluate."
            yield "done", self._results
            return

        yield "status", "Running scenarios:\n" + "\n".join(
            [scenario.scenario for scenario in self._scenarios.scenarios]
        )
        try:
            async for update_type, data in arun_evaluator_agent(
                evaluated_agent_url=str(self._evaluated_agent_url),
                auth_type=self._evaluated_agent_auth_type,
                auth_credentials=self._evaluated_agent_auth_credentials,
                judge_llm=self._judge_llm,
                judge_llm_api_key=self._judge_llm_api_key,
                scenarios=self._scenarios,
                business_context=self._business_context,
                deep_test_mode=self._deep_test_mode,
            ):
                if update_type == "results":
                    results = data
                    if results and results.results:
                        for res in results.results:
                            self._results.add_result(res)
                else:  # it's a 'chat' or 'status' update
                    yield update_type, data
        except Exception:
            logger.exception("Error evaluating scenarios")
            yield "status", "Error running scenarios"

        yield "done", self._results
