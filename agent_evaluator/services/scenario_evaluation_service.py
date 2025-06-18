from pathlib import Path

from loguru import logger

from ..evaluator_agent.run_evaluator_agent import run_evaluator_agent
from ..models.config import AuthType
from ..models.evaluation_result import EvaluationResults
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
        evaluation_results_output_path: Path,
    ):
        self._evaluated_agent_url = evaluated_agent_url
        self._evaluated_agent_auth_type = evaluated_agent_auth_type
        self._evaluated_agent_auth_credentials = evaluated_agent_auth_credentials
        self._judge_llm = judge_llm
        self._judge_llm_api_key = judge_llm_api_key
        self._scenarios = scenarios
        self._evaluation_results_output_path = evaluation_results_output_path

    def _evaluate_policy_scenarios(self) -> EvaluationResults | None:
        policy_scenarios = self._scenarios.get_policy_scenarios()
        try:
            return run_evaluator_agent(
                evaluated_agent_url=str(self._evaluated_agent_url),
                auth_type=self._evaluated_agent_auth_type,
                auth_credentials=self._evaluated_agent_auth_credentials,
                judge_llm=self._judge_llm,
                judge_llm_api_key=self._judge_llm_api_key,
                scenarios=policy_scenarios,
            )
        except Exception:
            logger.exception("Error evaluating policy scenarios")
            return None

    def _evaluate_prompt_injection_scenarios(self) -> EvaluationResults | None:
        pass

    def _evaluate_safety_scenarios(self) -> EvaluationResults | None:
        pass

    def _evaluate_grounding_scenarios(self) -> EvaluationResults | None:
        pass

    def evaluate_scenarios(self) -> EvaluationResults:
        policy_results = self._evaluate_policy_scenarios()
        prompt_injection_results = self._evaluate_prompt_injection_scenarios()
        safety_results = self._evaluate_safety_scenarios()
        grounding_results = self._evaluate_grounding_scenarios()

        combined_results = EvaluationResults.combine(
            policy_results,
            prompt_injection_results,
            safety_results,
            grounding_results,
        )

        self._evaluation_results_output_path.write_text(
            combined_results.model_dump_json(indent=2, exclude_none=True),
            encoding="utf-8",
        )

        return combined_results
