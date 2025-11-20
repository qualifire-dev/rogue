"""
Evaluation orchestrator - Server-native evaluation logic.
"""

from typing import Any, AsyncGenerator, List, Optional, Tuple

from rogue_sdk.types import (
    AuthType,
    EvaluationMode,
    EvaluationResults,
    Protocol,
    Scenarios,
    Transport,
)

from ...common.logging import get_logger
from ...evaluator_agent.run_evaluator_agent import arun_evaluator_agent
from ..services.red_team_scenario_generator import RedTeamScenarioGenerator


class EvaluationOrchestrator:
    """
    Server-native evaluation orchestrator.

    This class handles the core evaluation logic that was previously
    in ScenarioEvaluationService, but is now integrated directly
    into the server architecture.
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
        judge_llm_aws_access_key_id: str | None = None,
        judge_llm_aws_secret_access_key: str | None = None,
        judge_llm_aws_region: str | None = None,
        evaluation_mode: Optional[EvaluationMode] = None,
        owasp_categories: Optional[List[str]] = None,
        attacks_per_category: int = 5,
    ):
        self.protocol = protocol
        self.transport = transport
        self.evaluated_agent_url = evaluated_agent_url
        self.evaluated_agent_auth_type = evaluated_agent_auth_type
        self.evaluated_agent_auth_credentials = evaluated_agent_auth_credentials
        self.judge_llm = judge_llm
        self.judge_llm_api_key = judge_llm_api_key
        self.judge_llm_aws_access_key_id = judge_llm_aws_access_key_id
        self.judge_llm_aws_secret_access_key = judge_llm_aws_secret_access_key
        self.judge_llm_aws_region = judge_llm_aws_region
        self.scenarios = scenarios
        self.business_context = business_context
        self.deep_test_mode = deep_test_mode
        self.evaluation_mode = evaluation_mode or EvaluationMode.POLICY
        self.owasp_categories = owasp_categories or []
        self.attacks_per_category = attacks_per_category
        self.results = EvaluationResults()
        self.logger = get_logger(__name__)

    async def run_evaluation(self) -> AsyncGenerator[Tuple[str, Any], None]:
        """
        Run the evaluation and yield progress updates.

        Yields:
            Tuple[str, Any]: (update_type, data) where update_type is one of:
                - "status": Status message string
                - "chat": Chat message dict
                - "results": EvaluationResults object
        """
        self.logger.info(
            "🎯 EvaluationOrchestrator starting evaluation",
            extra={
                "scenario_count": len(self.scenarios.scenarios),
                "agent_url": self.evaluated_agent_url,
                "judge_llm": self.judge_llm,
                "deep_test_mode": self.deep_test_mode,
                "evaluation_mode": (
                    self.evaluation_mode.value
                    if self.evaluation_mode
                    else EvaluationMode.POLICY.value
                ),
                "owasp_categories": self.owasp_categories,
            },
        )

        # For red team mode, generate scenarios for status display only
        # Red team agents don't need scenarios - they work with OWASP categories
        scenarios_for_status = self.scenarios
        scenarios_for_agent = self.scenarios

        if self.evaluation_mode == EvaluationMode.RED_TEAM:
            # In red team mode, always pass empty scenarios to agents
            # They work purely with OWASP categories
            scenarios_for_agent = Scenarios(scenarios=[])

            # Generate scenarios for status display if none provided
            if not self.scenarios.scenarios and self.owasp_categories:
                self.logger.info(
                    (
                        "🔴 Generating red team scenarios from OWASP categories "
                        "(for status display)"
                    ),
                    extra={"owasp_categories": self.owasp_categories},
                )
                generator = RedTeamScenarioGenerator()
                scenarios_for_status = await generator.generate_scenarios(
                    owasp_categories=self.owasp_categories,
                    business_context=self.business_context,
                    attacks_per_category=self.attacks_per_category,
                )
                scenario_count = len(scenarios_for_status.scenarios)
                self.logger.info(
                    f"🔴 Generated {scenario_count} red team scenarios",
                )

            # Check if we have OWASP categories
            if not self.owasp_categories:
                warning_msg = (
                    "⚠️ No OWASP categories provided for red team evaluation"
                )
                self.logger.warning(warning_msg)
                yield "status", "No OWASP categories provided for red team evaluation."
                yield "results", self.results
                return
        else:
            # Policy mode: use provided scenarios
            if not self.scenarios.scenarios:
                self.logger.warning("⚠️ No scenarios to evaluate")
                yield "status", "No scenarios to evaluate."
                yield "results", self.results
                return

        # Prepare status message
        mode_prefix = (
            "🔴" if self.evaluation_mode == EvaluationMode.RED_TEAM else "📋"
        )
        if scenarios_for_status.scenarios:
            scenario_list = [
                scenario.scenario for scenario in scenarios_for_status.scenarios
            ]
            status_msg = f"{mode_prefix} Running scenarios:\n" + "\n".join(
                scenario_list,
            )
        else:
            categories_str = ", ".join(self.owasp_categories)
            status_msg = (
                f"{mode_prefix} Running red team evaluation with "
                f"OWASP categories: {categories_str}"
            )
        self.logger.info(
            f"{mode_prefix} Starting evaluation",
            extra={
                "scenario_count": (
                    len(scenarios_for_status.scenarios)
                    if scenarios_for_status.scenarios
                    else 0
                ),
                "owasp_categories": self.owasp_categories,
            },
        )
        yield "status", status_msg

        try:
            self.logger.info("🤖 Starting evaluator agent")
            update_count = 0

            # Call the evaluator agent directly
            # Pass empty scenarios for red team mode, actual scenarios for policy mode
            async for update_type, data in arun_evaluator_agent(
                protocol=self.protocol,
                transport=self.transport,
                evaluated_agent_url=self.evaluated_agent_url,
                auth_type=self.evaluated_agent_auth_type,
                auth_credentials=self.evaluated_agent_auth_credentials,
                judge_llm=self.judge_llm,
                judge_llm_api_key=self.judge_llm_api_key,
                judge_llm_aws_access_key_id=self.judge_llm_aws_access_key_id,
                judge_llm_aws_secret_access_key=self.judge_llm_aws_secret_access_key,
                judge_llm_aws_region=self.judge_llm_aws_region,
                scenarios=scenarios_for_agent,
                business_context=self.business_context,
                deep_test_mode=self.deep_test_mode,
                evaluation_mode=self.evaluation_mode,
                owasp_categories=self.owasp_categories,
            ):
                update_count += 1
                self.logger.info(
                    f"📨 EvaluationOrchestrator received update #{update_count}",
                    extra={
                        "update_type": update_type,
                        "data_type": type(data).__name__,
                        "data_preview": str(data)[:100] if data else "None",
                    },
                )

                if update_type == "results":
                    # Process results
                    results = data
                    if results and results.results:
                        self.logger.info(
                            f"📊 Processing {len(results.results)} evaluation results",
                        )
                        for res in results.results:
                            self.results.add_result(res)
                    else:
                        self.logger.warning(
                            "⚠️ Received results update but no results data",
                        )

                    # Yield the accumulated results
                    yield "results", self.results
                else:
                    # Forward chat and status updates
                    self.logger.debug(
                        f"🔄 Forwarding {update_type} update: {str(data)[:50]}...",
                    )
                    yield update_type, data

            self.logger.info(f"🏁 Evaluation completed. Total updates: {update_count}")

        except Exception as e:
            self.logger.exception("❌ Evaluation failed")

            error_msg = f"Evaluation failed: {str(e)}"

            # Check for specific error types
            if "timeout" in error_msg.lower():
                error_msg = (
                    "Evaluation timed out. Please check your agent configuration "
                    "and try again."
                )
            elif "connection" in error_msg.lower():
                error_msg = (
                    "Failed to connect to the agent. Please verify the agent URL "
                    "and authentication."
                )
            elif "authentication" in error_msg.lower():
                error_msg = "Authentication failed. Please check your credentials."

            yield "status", f"❌ {error_msg}"
            yield "results", self.results

        finally:
            self.logger.info(
                "✅ EvaluationOrchestrator completed",
                extra={
                    "total_results": len(self.results.results),
                    "evaluation_successful": len(self.results.results) > 0,
                },
            )
