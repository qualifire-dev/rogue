"""
Scenario Evaluation Service.

Handles policy-based scenario evaluation. Red team evaluation is
now handled by the EvaluationOrchestrator using the server's
red_teaming module.
"""

from typing import Any, AsyncGenerator

from loguru import logger
from rogue_sdk.types import (
    AuthType,
    EvaluationMode,
    EvaluationResults,
    Protocol,
    Scenarios,
    Transport,
)

from ...evaluator_agent.run_evaluator_agent import arun_evaluator_agent


class ScenarioEvaluationService:
    """
    Service for policy-based scenario evaluation.

    Note: Red team evaluation should use EvaluationOrchestrator directly,
    which uses the server's red_teaming module.
    """

    def __init__(
        self,
        protocol: Protocol,
        transport: Transport | None,
        evaluated_agent_url: str,
        evaluated_agent_auth_type: AuthType,
        evaluated_agent_auth_credentials: str | None,
        judge_llm: str,
        judge_llm_api_key: str | None,
        scenarios: Scenarios,
        business_context: str,
        deep_test_mode: bool,
    ):
        self._protocol = protocol
        self._transport = transport
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
        """
        Evaluate policy scenarios.

        Yields:
            Tuples of (update_type, data) where update_type is:
            - "status": Status message string
            - "chat": Chat message dict
            - "done": Final EvaluationResults
        """
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

        # Prepare status message
        scenario_list = [scenario.scenario for scenario in self._scenarios.scenarios]
        status_msg = "📋 Running scenarios:\n" + "\n".join(scenario_list)
        logger.info(
            "📋 Starting policy evaluation",
            extra={"scenario_count": len(self._scenarios.scenarios)},
        )
        yield "status", status_msg

        try:
            logger.info("🤖 Calling arun_evaluator_agent")
            update_count = 0

            async for update_type, data in arun_evaluator_agent(
                protocol=self._protocol,
                transport=self._transport,
                evaluated_agent_url=str(self._evaluated_agent_url),
                auth_type=self._evaluated_agent_auth_type,
                auth_credentials=self._evaluated_agent_auth_credentials,
                judge_llm=self._judge_llm,
                judge_llm_api_key=self._judge_llm_api_key,
                scenarios=self._scenarios,
                business_context=self._business_context,
                deep_test_mode=self._deep_test_mode,
                evaluation_mode=EvaluationMode.POLICY,
            ):
                update_count += 1
                logger.debug(
                    f"📨 Received update #{update_count}",
                    extra={
                        "update_type": update_type,
                        "data_type": type(data).__name__,
                    },
                )

                if update_type == "results":
                    results = data
                    if results and results.results:
                        for res in results.results:
                            self._results.add_result(res)
                else:
                    yield update_type, data

            logger.info(f"🏁 Evaluation completed. Total updates: {update_count}")

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)

            logger.exception(
                "💥 Error evaluating scenarios",
                extra={
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
                    f"🔐 LLM Authentication Error: "
                    f"Invalid API key for {self._judge_llm}."
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
            f"✅ ScenarioEvaluationService completed with "
            f"{len(self._results.results)} results",
        )
        yield "done", self._results
