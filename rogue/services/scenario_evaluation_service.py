from pathlib import Path
from typing import AsyncGenerator, Any

from loguru import logger

from ..evaluator_agent.run_evaluator_agent import arun_evaluator_agent
from ..models.config import AuthType
from ..models.evaluation_result import (
    EvaluationResults,
    EvaluationResult,
    ConversationEvaluation,
)
from ..models.scenario import Scenarios
from ..prompt_injection_evaluator.run_prompt_injection_evaluator import (
    arun_prompt_injection_evaluator,
)


class ScenarioEvaluationService:
    MAX_SAMPLES = 10

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
        deep_test_mode: bool,
    ):
        self._evaluated_agent_url = evaluated_agent_url
        self._evaluated_agent_auth_type = evaluated_agent_auth_type
        self._evaluated_agent_auth_credentials = evaluated_agent_auth_credentials
        self._judge_llm = judge_llm
        self._judge_llm_api_key = judge_llm_api_key
        self._scenarios = scenarios
        self._evaluation_results_output_path = evaluation_results_output_path
        self._business_context = business_context
        self._deep_test_mode = deep_test_mode
        self._results = EvaluationResults()

    async def _evaluate_policy_scenarios(self) -> AsyncGenerator[tuple[str, Any], None]:
        for scenario in self._scenarios.get_policy_scenarios().scenarios:
            yield "status", f"Running policy scenario: {scenario.scenario}"
            try:
                async for update_type, data in arun_evaluator_agent(
                    evaluated_agent_url=str(self._evaluated_agent_url),
                    auth_type=self._evaluated_agent_auth_type,
                    auth_credentials=self._evaluated_agent_auth_credentials,
                    judge_llm=self._judge_llm,
                    judge_llm_api_key=self._judge_llm_api_key,
                    scenarios=Scenarios(scenarios=[scenario]),
                    business_context=self._business_context,
                    deep_test_mode=self._deep_test_mode,
                ):
                    if update_type == "results":
                        results = data
                        if results and results.results:
                            self._results.add_result(results.results[0])
                    else:  # it's a 'chat' update
                        yield update_type, data
            except Exception:
                logger.exception(
                    "Error evaluating policy scenario",
                    extra={"scenario": scenario},
                )
                yield "status", f"Error running scenario: {scenario.scenario}"
                continue

    async def _evaluate_prompt_injection_scenarios(
        self,
    ) -> AsyncGenerator[tuple[str, Any], None]:
        for scenario in self._scenarios.get_prompt_injection_scenarios().scenarios:
            yield "status", f"Running prompt injection scenario: {scenario.scenario}"
            try:
                if not scenario.dataset:
                    logger.warning(
                        "Prompt injection scenario is missing dataset, skipping",
                        extra={"scenario": scenario},
                    )
                    continue

                # dataset name is in scenario.scenario
                dataset_name = scenario.dataset
                async for update_type, data in arun_prompt_injection_evaluator(
                    evaluated_agent_url=self._evaluated_agent_url,
                    auth_type=self._evaluated_agent_auth_type,
                    auth_credentials=self._evaluated_agent_auth_credentials,
                    judge_llm=self._judge_llm,
                    judge_llm_api_key=self._judge_llm_api_key,
                    dataset_name=dataset_name,
                    max_samples=self.MAX_SAMPLES,
                ):
                    if update_type == "result":
                        # Convert PromptInjectionEvaluation to EvaluationResult
                        injection_eval = data
                        eval_result = EvaluationResult(
                            scenario=scenario,
                            conversations=[
                                ConversationEvaluation(
                                    messages=injection_eval.conversation_history,
                                    passed=injection_eval.passed,
                                    reason=injection_eval.reason,
                                )
                            ],
                            passed=injection_eval.passed,
                        )
                        self._results.add_result(eval_result)
                    elif update_type == "status":
                        yield "status", data
                    else:
                        yield update_type, data

            except Exception:
                logger.exception(
                    "Error evaluating prompt injection scenario",
                    extra={"scenario": scenario},
                )
                yield "status", f"Error running scenario: {scenario.scenario}"
                continue

    def _evaluate_safety_scenarios(self) -> EvaluationResults | None:
        pass

    def _evaluate_grounding_scenarios(self) -> EvaluationResults | None:
        pass

    async def evaluate_scenarios(self) -> AsyncGenerator[tuple[str, Any], None]:
        # TODO: Implement this for all scenario types
        async for status, data in self._evaluate_policy_scenarios():
            yield status, data

        async for status, data in self._evaluate_prompt_injection_scenarios():
            yield status, data

        all_results = self._results
        self._evaluation_results_output_path.write_text(
            all_results.model_dump_json(indent=2, exclude_none=True),
            encoding="utf-8",
        )

        yield "done", all_results
