from typing import Any, AsyncGenerator, List, Optional

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
from .red_team_scenario_generator import RedTeamScenarioGenerator


class ScenarioEvaluationService:
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
        evaluation_mode: EvaluationMode = EvaluationMode.POLICY,
        owasp_categories: Optional[List[str]] = None,
        attacks_per_category: int = 5,
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
        self._evaluation_mode = evaluation_mode
        self._owasp_categories = owasp_categories or []
        self._attacks_per_category = attacks_per_category
        self._results = EvaluationResults()

    async def evaluate_scenarios(self) -> AsyncGenerator[tuple[str, Any], None]:
        logger.info(
            "🎯 ScenarioEvaluationService.evaluate_scenarios starting",
            extra={
                "scenario_count": len(self._scenarios.scenarios),
                "agent_url": self._evaluated_agent_url,
                "judge_llm": self._judge_llm,
                "deep_test_mode": self._deep_test_mode,
                "evaluation_mode": self._evaluation_mode.value,
                "owasp_categories": self._owasp_categories,
            },
        )

        # Generate scenarios if in red team mode and none provided
        scenarios_to_use = self._scenarios
        if (
            self._evaluation_mode == EvaluationMode.RED_TEAM
            and not self._scenarios.scenarios
            and self._owasp_categories
        ):
            logger.info(
                "🔴 Generating red team scenarios from OWASP categories",
                extra={"owasp_categories": self._owasp_categories},
            )
            generator = RedTeamScenarioGenerator()
            scenarios_to_use = await generator.generate_scenarios(
                owasp_categories=self._owasp_categories,
                business_context=self._business_context,
                attacks_per_category=self._attacks_per_category,
            )
            logger.info(
                f"🔴 Generated {len(scenarios_to_use.scenarios)} red team scenarios",
            )

        if not scenarios_to_use.scenarios:
            logger.warning("⚠️ No scenarios to evaluate")
            yield "status", "No scenarios to evaluate."
            yield "done", self._results
            return

        scenario_list = [scenario.scenario for scenario in scenarios_to_use.scenarios]
        mode_prefix = "🔴" if self._evaluation_mode == EvaluationMode.RED_TEAM else "📋"
        status_msg = f"{mode_prefix} Running scenarios:\n" + "\n".join(scenario_list)
        logger.info(
            f"{mode_prefix} Starting evaluation of {len(scenario_list)} scenarios",
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
                scenarios=scenarios_to_use,
                business_context=self._business_context,
                deep_test_mode=self._deep_test_mode,
                evaluation_mode=self._evaluation_mode,
                owasp_categories=(
                    self._owasp_categories if self._owasp_categories else None
                ),
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
