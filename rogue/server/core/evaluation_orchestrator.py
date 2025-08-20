"""
Evaluation orchestrator - Server-native evaluation logic.
"""

from typing import Any, AsyncGenerator, Tuple

from rogue_sdk.types import AuthType, EvaluationResults, Scenarios

from ...common.logging import get_logger
from ...evaluator_agent.run_evaluator_agent import arun_evaluator_agent


class EvaluationOrchestrator:
    """
    Server-native evaluation orchestrator.

    This class handles the core evaluation logic that was previously
    in ScenarioEvaluationService, but is now integrated directly
    into the server architecture.
    """

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
        self.evaluated_agent_url = evaluated_agent_url
        self.evaluated_agent_auth_type = evaluated_agent_auth_type
        self.evaluated_agent_auth_credentials = evaluated_agent_auth_credentials
        self.judge_llm = judge_llm
        self.judge_llm_api_key = judge_llm_api_key
        self.scenarios = scenarios
        self.business_context = business_context
        self.deep_test_mode = deep_test_mode
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
            },
        )

        if not self.scenarios.scenarios:
            self.logger.warning("⚠️ No scenarios to evaluate")
            yield "status", "No scenarios to evaluate."
            yield "results", self.results
            return

        # Prepare status message
        scenario_list = [scenario.scenario for scenario in self.scenarios.scenarios]
        status_msg = "Running scenarios:\n" + "\n".join(scenario_list)
        self.logger.info(f"📋 Starting evaluation of {len(scenario_list)} scenarios")
        yield "status", status_msg

        try:
            self.logger.info("🤖 Starting evaluator agent")
            update_count = 0

            # Call the evaluator agent directly
            async for update_type, data in arun_evaluator_agent(
                evaluated_agent_url=self.evaluated_agent_url,
                auth_type=self.evaluated_agent_auth_type,
                auth_credentials=self.evaluated_agent_auth_credentials,
                judge_llm=self.judge_llm,
                judge_llm_api_key=self.judge_llm_api_key,
                scenarios=self.scenarios,
                business_context=self.business_context,
                deep_test_mode=self.deep_test_mode,
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
