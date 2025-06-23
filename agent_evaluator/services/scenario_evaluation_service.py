from pathlib import Path
from typing import Iterator

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
        business_context: str,
    ):
        self._evaluated_agent_url = evaluated_agent_url
        self._evaluated_agent_auth_type = evaluated_agent_auth_type
        self._evaluated_agent_auth_credentials = evaluated_agent_auth_credentials
        self._judge_llm = judge_llm
        self._judge_llm_api_key = judge_llm_api_key
        self._scenarios = scenarios
        self._evaluation_results_output_path = evaluation_results_output_path
        self._business_context = business_context

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
                business_context=self._business_context,
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

    def evaluate_scenarios(self) -> Iterator[str | EvaluationResults]:
        all_results = EvaluationResults()

        # TODO: Implement this for all scenario types
        for scenario in self._scenarios.scenarios:
            yield f"Running scenario: {scenario.scenario}"
            try:
                scenarios = Scenarios(scenarios=[scenario])
                results = run_evaluator_agent(
                    evaluated_agent_url=str(self._evaluated_agent_url),
                    auth_type=self._evaluated_agent_auth_type,
                    auth_credentials=self._evaluated_agent_auth_credentials,
                    judge_llm=self._judge_llm,
                    judge_llm_api_key=self._judge_llm_api_key,
                    scenarios=scenarios,
                    business_context=self._business_context,
                )
                if results:
                    all_results.add_result(results.results[0])
            except Exception:
                logger.exception(f"Error evaluating scenario: {scenario.scenario}")
                # Optionally yield an error status
                yield f"Error running scenario: {scenario.scenario}"

        self._evaluation_results_output_path.write_text(
            all_results.model_dump_json(indent=2, exclude_none=True),
            encoding="utf-8",
        )

        yield all_results
