"""Factory for creating red team attacker agents."""

from typing import Optional

from loguru import logger
from rogue_sdk.types import AuthType, Protocol, Transport

from .a2a_red_team_attacker_agent import A2ARedTeamAttackerAgent
from .base_red_team_attacker_agent import BaseRedTeamAttackerAgent
from .mcp_red_team_attacker_agent import MCPRedTeamAttackerAgent


def create_red_team_attacker_agent(
    protocol: Protocol,
    transport: Optional[Transport],
    evaluated_agent_url: str,
    evaluated_agent_auth_type: AuthType,
    evaluated_agent_auth_credentials: Optional[str],
    red_team_config,  # RedTeamConfig from rogue_sdk.types
    business_context: str,
    attacker_llm: str,
    attacker_llm_auth: Optional[str],
    attacker_llm_aws_access_key_id: Optional[str] = None,
    attacker_llm_aws_secret_access_key: Optional[str] = None,
    attacker_llm_aws_region: Optional[str] = None,
    judge_llm: str = "gpt-4",
    judge_llm_auth: Optional[str] = None,
    judge_llm_aws_access_key_id: Optional[str] = None,
    judge_llm_aws_secret_access_key: Optional[str] = None,
    judge_llm_aws_region: Optional[str] = None,
    qualifire_api_key: Optional[str] = None,
) -> BaseRedTeamAttackerAgent:
    """
    Create a red team attacker agent based on the protocol.

    Args:
        protocol: The protocol to use (A2A or MCP)
        transport: Optional transport type for MCP
        evaluated_agent_url: URL of the agent to attack
        evaluated_agent_auth_type: Authentication type for the evaluated agent
        evaluated_agent_auth_credentials: Authentication credentials
        red_team_config: Full red team configuration
        business_context: Context about the agent being tested
        attacker_llm: LLM model to use for generating attacks
        attacker_llm_auth: Authentication for attacker LLM
        attacker_llm_aws_access_key_id: AWS credentials for attacker LLM
        attacker_llm_aws_secret_access_key: AWS credentials for attacker LLM
        attacker_llm_aws_region: AWS region for attacker LLM
        judge_llm: LLM model to use for evaluating responses
        judge_llm_auth: Authentication for judge LLM
        judge_llm_aws_access_key_id: AWS credentials for judge LLM
        judge_llm_aws_secret_access_key: AWS credentials for judge LLM
        judge_llm_aws_region: AWS region for judge LLM
        qualifire_api_key: Optional API key for premium features

    Returns:
        A red team attacker agent instance

    Raises:
        ValueError: If the protocol is not supported
    """
    logger.info(
        f"Creating red team attacker agent for protocol: {protocol.value}",
        extra={
            "scan_type": red_team_config.scan_type,
            "vulnerabilities_count": len(red_team_config.vulnerabilities),
            "attacks_count": len(red_team_config.attacks),
        },
    )

    common_kwargs = {
        "evaluated_agent_address": evaluated_agent_url,
        "protocol": protocol,
        "transport": transport,
        "auth_type": evaluated_agent_auth_type,
        "auth_credentials": evaluated_agent_auth_credentials,
        "red_team_config": red_team_config,
        "business_context": business_context,
        "attacker_llm": attacker_llm,
        "attacker_llm_auth": attacker_llm_auth,
        "attacker_llm_aws_access_key_id": attacker_llm_aws_access_key_id,
        "attacker_llm_aws_secret_access_key": attacker_llm_aws_secret_access_key,
        "attacker_llm_aws_region": attacker_llm_aws_region,
        "judge_llm": judge_llm,
        "judge_llm_auth": judge_llm_auth,
        "judge_llm_aws_access_key_id": judge_llm_aws_access_key_id,
        "judge_llm_aws_secret_access_key": judge_llm_aws_secret_access_key,
        "judge_llm_aws_region": judge_llm_aws_region,
        "qualifire_api_key": qualifire_api_key,
    }

    if protocol == Protocol.A2A:
        return A2ARedTeamAttackerAgent(**common_kwargs)
    elif protocol == Protocol.MCP:
        return MCPRedTeamAttackerAgent(**common_kwargs)
    else:
        raise ValueError(f"Unsupported protocol for red team attacks: {protocol}")
