"""
Red Team Orchestrator - Coordinates red team scans using attacker agents.

This orchestrator uses agent-based attack generation instead of programmatic
attack generation, providing more creative and adaptive testing.
"""

from typing import Any, AsyncGenerator, Optional, Tuple

from rogue_sdk.types import (
    AuthType,
    Protocol,
    RedTeamConfig,
    Transport,
)

from ...common.logging import get_logger
from ...evaluator_agent.red_team.factory import create_red_team_attacker_agent

logger = get_logger(__name__)


class RedTeamOrchestrator:
    """
    Red team orchestrator using attacker agents.

    This orchestrator coordinates red team scans by:
    1. Using RedTeamAttackerAgent to generate and send creative attacks
    2. Using judge LLM to evaluate responses for vulnerabilities
    3. Tracking results and generating compliance reports
    """

    def __init__(
        self,
        protocol: Protocol,
        transport: Optional[Transport],
        evaluated_agent_url: str,
        evaluated_agent_auth_type: AuthType,
        evaluated_agent_auth_credentials: Optional[str],
        red_team_config: RedTeamConfig,
        qualifire_api_key: Optional[str],
        judge_llm: str,
        judge_llm_api_key: Optional[str],
        judge_llm_aws_access_key_id: Optional[str] = None,
        judge_llm_aws_secret_access_key: Optional[str] = None,
        judge_llm_aws_region: Optional[str] = None,
        attacker_llm: str = "gpt-4",
        attacker_llm_api_key: Optional[str] = None,
        attacker_llm_aws_access_key_id: Optional[str] = None,
        attacker_llm_aws_secret_access_key: Optional[str] = None,
        attacker_llm_aws_region: Optional[str] = None,
        business_context: str = "",
    ):
        self.protocol = protocol
        self.transport = transport
        self.evaluated_agent_url = evaluated_agent_url
        self.evaluated_agent_auth_type = evaluated_agent_auth_type
        self.evaluated_agent_auth_credentials = evaluated_agent_auth_credentials
        self.red_team_config = red_team_config
        self.qualifire_api_key = qualifire_api_key
        self.judge_llm = judge_llm
        self.judge_llm_api_key = judge_llm_api_key
        self.judge_llm_aws_access_key_id = judge_llm_aws_access_key_id
        self.judge_llm_aws_secret_access_key = judge_llm_aws_secret_access_key
        self.judge_llm_aws_region = judge_llm_aws_region
        self.attacker_llm = attacker_llm
        self.attacker_llm_api_key = attacker_llm_api_key
        self.attacker_llm_aws_access_key_id = attacker_llm_aws_access_key_id
        self.attacker_llm_aws_secret_access_key = attacker_llm_aws_secret_access_key
        self.attacker_llm_aws_region = attacker_llm_aws_region
        self.business_context = business_context
        self.logger = get_logger(__name__)

        # Create attacker agent
        self.attacker_agent = create_red_team_attacker_agent(
            protocol=protocol,
            transport=transport,
            evaluated_agent_url=evaluated_agent_url,
            evaluated_agent_auth_type=evaluated_agent_auth_type,
            evaluated_agent_auth_credentials=evaluated_agent_auth_credentials,
            red_team_config=red_team_config,
            business_context=business_context,
            attacker_llm=attacker_llm,
            attacker_llm_auth=attacker_llm_api_key,
            attacker_llm_aws_access_key_id=attacker_llm_aws_access_key_id,
            attacker_llm_aws_secret_access_key=attacker_llm_aws_secret_access_key,
            attacker_llm_aws_region=attacker_llm_aws_region,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_api_key,
            judge_llm_aws_access_key_id=judge_llm_aws_access_key_id,
            judge_llm_aws_secret_access_key=judge_llm_aws_secret_access_key,
            judge_llm_aws_region=judge_llm_aws_region,
            qualifire_api_key=qualifire_api_key,
        )

    async def run_scan(self) -> AsyncGenerator[Tuple[str, Any], None]:
        """
        Run the red team scan and yield progress updates.

        Yields:
            Tuple[str, Any]: (update_type, data) where update_type is:
                - "status": Status message string
                - "chat": Chat message dict
                - "results": RedTeamResults object
        """
        self.logger.info(
            "🔴 RedTeamOrchestrator starting scan",
            extra={
                "vulnerabilities_count": len(self.red_team_config.vulnerabilities),
                "attacks_count": len(self.red_team_config.attacks),
                "agent_url": self.evaluated_agent_url,
                "protocol": self.protocol.value,
                "judge_llm": self.judge_llm,
                "attacker_llm": self.attacker_llm,
            },
        )

        yield "status", (
            f"🔴 Starting red team scan\n"
            f"  Scan Type: {self.red_team_config.scan_type}\n"
            f"  Vulnerabilities: {len(self.red_team_config.vulnerabilities)}\n"
            f"  Attacks: {len(self.red_team_config.attacks)}\n"
            f"  Target: {self.evaluated_agent_url}"
        )

        try:
            # Run the attacker agent
            async with self.attacker_agent:
                # Stream updates from the attacker agent
                async for update_type, data in self.attacker_agent.run():
                    if update_type == "status":
                        self.logger.debug(f"Status update: {data}")
                        yield "status", data
                    elif update_type == "chat":
                        self.logger.debug("Chat update received")
                        yield "chat", data
                    elif update_type == "vulnerability_result":
                        self.logger.info(
                            f"Vulnerability result: {data.get('vulnerability_id')}",
                        )
                        yield "status", f"✓ Completed testing: {data.get('vulnerability_id')}"  # noqa: E501
                    elif update_type == "results":
                        self.logger.info("✅ Red team scan completed")
                        yield "results", data
                        return

                # If we get here without results, something went wrong
                self.logger.warning("Red team scan completed without final results")

        except Exception:
            self.logger.exception("❌ Red team scan failed")
            raise
