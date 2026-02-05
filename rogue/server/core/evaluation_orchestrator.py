"""
Evaluation orchestrator - Server-native policy evaluation logic.

Handles policy-based scenario evaluation. Red team evaluation is now
handled by the separate RedTeamOrchestrator.
"""

from typing import Any, AsyncGenerator

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


class EvaluationOrchestrator:
    """
    Server-native policy evaluation orchestrator.

    Handles scenario-based testing of business rules and policies.
    Red team evaluation is handled by the separate RedTeamOrchestrator.
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
        judge_llm_api_base: str | None = None,
        judge_llm_api_version: str | None = None,
        python_entrypoint_file: str | None = None,
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
        self.judge_llm_api_base = judge_llm_api_base
        self.judge_llm_api_version = judge_llm_api_version
        self.scenarios = scenarios
        self.business_context = business_context
        self.deep_test_mode = deep_test_mode
        self.python_entrypoint_file = python_entrypoint_file
        self.results = EvaluationResults()
        self.logger = get_logger(__name__)

    async def run_evaluation(self) -> AsyncGenerator[tuple[str, Any], None]:
        """
        Run the policy evaluation and yield progress updates.

        Yields:
            Tuple[str, Any]: (update_type, data) where update_type is one of:
                - "status": Status message string
                - "chat": Chat message dict
                - "results": EvaluationResults object
        """
        self.logger.info(
            "🎯 EvaluationOrchestrator starting policy evaluation",
            extra={
                "scenario_count": len(self.scenarios.scenarios),
                "agent_url": self.evaluated_agent_url,
                "judge_llm": self.judge_llm,
                "deep_test_mode": self.deep_test_mode,
                "protocol": self.protocol.value if self.protocol else None,
                "python_entrypoint_file": self.python_entrypoint_file,
            },
        )

        # Run policy evaluation
        async for update in self._run_policy_evaluation():
            yield update

    async def _run_policy_evaluation(self) -> AsyncGenerator[tuple[str, Any], None]:
        """Run policy-based scenario evaluation."""
        if not self.scenarios.scenarios:
            self.logger.warning("⚠️ No scenarios to evaluate")
            yield "status", "No scenarios to evaluate."
            yield "results", self.results
            return

        # Prepare status message
        scenario_list = [scenario.scenario for scenario in self.scenarios.scenarios]
        status_msg = "📋 Running scenarios:\n" + "\n".join(scenario_list)
        self.logger.info(
            "📋 Starting policy evaluation",
            extra={"scenario_count": len(self.scenarios.scenarios)},
        )
        yield "status", status_msg

        try:
            self.logger.info("🤖 Starting evaluator agent")
            update_count = 0

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
                scenarios=self.scenarios,
                business_context=self.business_context,
                deep_test_mode=self.deep_test_mode,
                evaluation_mode=EvaluationMode.POLICY,
                python_entrypoint_file=self.python_entrypoint_file,
                judge_llm_api_base=self.judge_llm_api_base,
                judge_llm_api_version=self.judge_llm_api_version,
            ):
                update_count += 1
                self.logger.debug(
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
                            self.results.add_result(res)
                    yield "results", self.results
                else:
                    yield update_type, data

            self.logger.info(f"🏁 Policy evaluation completed. Updates: {update_count}")

        except Exception as e:
            self.logger.exception("❌ Policy evaluation failed")
            yield "status", f"❌ Evaluation failed: {str(e)}"
            yield "results", self.results
