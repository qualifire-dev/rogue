from typing import AsyncGenerator, Any

from loguru import logger

from ..evaluator_agent.run_evaluator_agent import arun_evaluator_agent
from ..models.config import AuthType
from ..models.evaluation_result import (
    PolicyEvaluationResult,
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
        self._results = PolicyEvaluationResult()

    async def evaluate_scenarios(self) -> AsyncGenerator[tuple[str, Any], None]:
        logger.info(
            "🎯 ScenarioEvaluationService.evaluate_scenarios starting",
            extra={
                "scenario_count": len(self._scenarios.scenarios),
                "agent_url": self._evaluated_agent_url,
                "judge_llm": self._judge_llm,
                "deep_test_mode": self._deep_test_mode,
            },
        )

        if not self._scenarios.scenarios:
            logger.warning("⚠️ No scenarios to evaluate")
            yield "status", "No scenarios to evaluate."
            yield "done", self._results
            return

        scenario_list = [scenario.scenario for scenario in self._scenarios.scenarios]
        status_msg = "Running scenarios:\n" + "\n".join(scenario_list)
        logger.info(f"📋 Starting evaluation of {len(scenario_list)} scenarios")
        yield "status", status_msg

        try:
            logger.info("🤖 Calling arun_evaluator_agent")
            update_count = 0

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
                update_count += 1
                logger.info(
                    f"📨 ScenarioEvaluationService received update #{update_count}",
                    extra={
                        "update_type": update_type,
                        "data_type": type(data).__name__,
                        "data_preview": str(data)[:100] if data else "None",
                    },
                )

                if update_type == "results":
                    results = data
                    if results and results.results:
                        logger.info(
                            f"📊 Processing {len(results.results)} evaluation results",
                        )
                        for res in results.results:
                            self._results.add_result(res)
                    else:
                        logger.warning("⚠️ Received results update but no results data")
                else:  # it's a 'chat' or 'status' update
                    logger.debug(
                        f"🔄 Forwarding {update_type} update: {str(data)[:50]}...",
                    )
                    yield update_type, data

            logger.info(
                f"🏁 arun_evaluator_agent completed. Total updates: {update_count}",
            )

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)

            logger.error(
                f"💥 Error evaluating scenarios: {e}",
                extra={
                    "error_type": error_type,
                    "agent_url": self._evaluated_agent_url,
                    "scenario_count": len(self._scenarios.scenarios),
                },
            )

            # Provide specific error messages for common issues
            if "APIError" in error_type and "Connection error" in error_msg:
                user_friendly_error = (
                    f"❌ LLM API Connection Error: Cannot connect to {self._judge_llm}. "
                    "Please check your API key and network connection."
                )
            elif "APIError" in error_type and "authentication" in error_msg.lower():
                user_friendly_error = (
                    "🔐 LLM Authentication Error: Invalid API key for "
                    f"{self._judge_llm}. Please check your "
                    "judge_llm_api_key configuration."
                )
            elif "timeout" in error_msg.lower():
                user_friendly_error = (
                    "⏰ Timeout Error: The evaluation took too long. "
                    "The agent under test may not be responding."
                )
            else:
                user_friendly_error = f"❌ Evaluation Error: {error_msg}"

            yield "status", user_friendly_error

        logger.info(
            (
                "✅ ScenarioEvaluationService completed with "
                f"{len(self._results.results)} total results"
            ),
        )
        yield "done", self._results
