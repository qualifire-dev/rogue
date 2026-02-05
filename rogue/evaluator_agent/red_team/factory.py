"""Factory for creating red team attacker agents."""

from typing import Optional, TypedDict

from loguru import logger
from rogue_sdk.types import AuthType, Protocol, RedTeamConfig, Transport

from ...server.red_teaming.models import RedTeamConfig as InternalRedTeamConfig
from .a2a_red_team_attacker_agent import A2ARedTeamAttackerAgent
from .base_red_team_attacker_agent import BaseRedTeamAttackerAgent
from .mcp_red_team_attacker_agent import MCPRedTeamAttackerAgent
from .python_red_team_attacker_agent import PythonRedTeamAttackerAgent


class _CommonKwargs(TypedDict):
    """Type definition for common kwargs passed to red team agents."""

    evaluated_agent_address: Optional[str]
    protocol: Protocol
    transport: Optional[Transport]
    auth_type: AuthType
    auth_credentials: Optional[str]
    red_team_config: InternalRedTeamConfig
    business_context: str
    attacker_llm: str
    attacker_llm_auth: Optional[str]
    attacker_llm_aws_access_key_id: Optional[str]
    attacker_llm_aws_secret_access_key: Optional[str]
    attacker_llm_aws_region: Optional[str]
    attacker_llm_api_base: Optional[str]
    attacker_llm_api_version: Optional[str]
    judge_llm: str
    judge_llm_auth: Optional[str]
    judge_llm_aws_access_key_id: Optional[str]
    judge_llm_aws_secret_access_key: Optional[str]
    judge_llm_aws_region: Optional[str]
    judge_llm_api_base: Optional[str]
    judge_llm_api_version: Optional[str]
    qualifire_api_key: Optional[str]


def create_red_team_attacker_agent(
    protocol: Protocol,
    transport: Optional[Transport],
    evaluated_agent_url: Optional[str] = None,
    evaluated_agent_auth_type: AuthType = AuthType.NO_AUTH,
    evaluated_agent_auth_credentials: Optional[str] = None,
    red_team_config: Optional[RedTeamConfig] = None,
    business_context: str = "",
    attacker_llm: str = "gpt-4",
    attacker_llm_auth: Optional[str] = None,
    attacker_llm_aws_access_key_id: Optional[str] = None,
    attacker_llm_aws_secret_access_key: Optional[str] = None,
    attacker_llm_aws_region: Optional[str] = None,
    attacker_llm_api_base: Optional[str] = None,
    attacker_llm_api_version: Optional[str] = None,
    judge_llm: str = "gpt-4",
    judge_llm_auth: Optional[str] = None,
    judge_llm_aws_access_key_id: Optional[str] = None,
    judge_llm_aws_secret_access_key: Optional[str] = None,
    judge_llm_aws_region: Optional[str] = None,
    judge_llm_api_base: Optional[str] = None,
    judge_llm_api_version: Optional[str] = None,
    qualifire_api_key: Optional[str] = None,
    python_entrypoint_file: Optional[str] = None,
) -> BaseRedTeamAttackerAgent:
    """
    Create a red team attacker agent based on the protocol.

    Args:
        protocol: The protocol to use (A2A, MCP, or PYTHON)
        transport: Optional transport type for MCP
        evaluated_agent_url: URL of the agent to attack (for A2A/MCP)
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
        python_entrypoint_file: Path to Python file with call_agent function
            (required for PYTHON protocol)

    Returns:
        A red team attacker agent instance

    Raises:
        ValueError: If the protocol is not supported
    """
    if red_team_config is None:
        raise ValueError("red_team_config is required")
    logger.info(
        f"Creating red team attacker agent for protocol: {protocol.value}",
        extra={
            "scan_type": red_team_config.scan_type,
            "vulnerabilities_count": len(red_team_config.vulnerabilities),
            "attacks_count": len(red_team_config.attacks),
        },
    )

    # Convert SDK RedTeamConfig to internal RedTeamConfig
    # Import internal ScanType for conversion
    from ...server.red_teaming.models import ScanType as InternalScanType

    internal_config = InternalRedTeamConfig(
        scan_type=InternalScanType(red_team_config.scan_type.value),
        vulnerabilities=red_team_config.vulnerabilities,
        attacks=red_team_config.attacks,
        attacks_per_vulnerability=red_team_config.attacks_per_vulnerability,
        frameworks=red_team_config.frameworks,
        random_seed=red_team_config.random_seed,
    )

    common_kwargs: _CommonKwargs = {
        "evaluated_agent_address": evaluated_agent_url,
        "protocol": protocol,
        "transport": transport,
        "auth_type": evaluated_agent_auth_type,
        "auth_credentials": evaluated_agent_auth_credentials,
        "red_team_config": internal_config,
        "business_context": business_context,
        "attacker_llm": attacker_llm,
        "attacker_llm_auth": attacker_llm_auth,
        "attacker_llm_aws_access_key_id": attacker_llm_aws_access_key_id,
        "attacker_llm_aws_secret_access_key": attacker_llm_aws_secret_access_key,
        "attacker_llm_aws_region": attacker_llm_aws_region,
        "attacker_llm_api_base": attacker_llm_api_base,
        "attacker_llm_api_version": attacker_llm_api_version,
        "judge_llm": judge_llm,
        "judge_llm_auth": judge_llm_auth,
        "judge_llm_aws_access_key_id": judge_llm_aws_access_key_id,
        "judge_llm_aws_secret_access_key": judge_llm_aws_secret_access_key,
        "judge_llm_aws_region": judge_llm_aws_region,
        "judge_llm_api_base": judge_llm_api_base,
        "judge_llm_api_version": judge_llm_api_version,
        "qualifire_api_key": qualifire_api_key,
    }

    if protocol == Protocol.A2A:
        if not evaluated_agent_url:
            raise ValueError("evaluated_agent_url is required for A2A protocol")
        return A2ARedTeamAttackerAgent(**common_kwargs)
    elif protocol == Protocol.MCP:
        if not evaluated_agent_url:
            raise ValueError("evaluated_agent_url is required for MCP protocol")
        return MCPRedTeamAttackerAgent(**common_kwargs)
    elif protocol == Protocol.PYTHON:
        if not python_entrypoint_file:
            raise ValueError(
                "python_entrypoint_file is required for PYTHON protocol",
            )
        return PythonRedTeamAttackerAgent(
            **common_kwargs,
            python_entrypoint_file=python_entrypoint_file,
        )
    else:
        raise ValueError(f"Unsupported protocol for red team attacks: {protocol}")
