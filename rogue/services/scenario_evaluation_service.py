import asyncio
from pathlib import Path
from typing import AsyncGenerator, Any

from loguru import logger

from ..evaluator_agent.run_evaluator_agent import arun_evaluator_agent
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

    async def _evaluate_single_policy_scenario(
        self,
        scenario,
        queue: asyncio.Queue,
    ):
        await queue.put(("status", f"Running policy scenario: {scenario.scenario}"))
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
                else:
                    await queue.put((update_type, data))
        except Exception:
            logger.exception(
                "Error evaluating policy scenario", extra={"scenario": scenario}
            )
            await queue.put(("status", f"Error running scenario: {scenario.scenario}"))

    async def _evaluate_policy_scenarios(self) -> AsyncGenerator[tuple[str, Any], None]:
        queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue()
        tasks = [
            asyncio.create_task(self._evaluate_single_policy_scenario(scenario, queue))
            for scenario in self._scenarios.get_policy_scenarios().scenarios
        ]

        async def queue_watcher():
            while any(not t.done() for t in tasks) or not queue.empty():
                try:
                    update = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield update
                except asyncio.TimeoutError:
                    continue

        async for item in queue_watcher():
            yield item

        await asyncio.gather(*tasks)

    def _evaluate_prompt_injection_scenarios(self) -> EvaluationResults | None:
        pass

    def _evaluate_safety_scenarios(self) -> EvaluationResults | None:
        pass

    def _evaluate_grounding_scenarios(self) -> EvaluationResults | None:
        pass

    async def evaluate_scenarios(self) -> AsyncGenerator[tuple[str, Any], None]:
        # TODO: Implement this for all scenario types
        async for status, data in self._evaluate_policy_scenarios():
            yield status, data

        self._evaluation_results_output_path.write_text(
            self._results.model_dump_json(indent=2, exclude_none=True),
            encoding="utf-8",
        )

        yield "results", self._results
