from typing import Callable, List, Optional

from rogue_sdk.types import EvaluationMode, Protocol, Scenarios, Transport

from .a2a.a2a_evaluator_agent import A2AEvaluatorAgent
from .base_evaluator_agent import BaseEvaluatorAgent
from .mcp.mcp_evaluator_agent import MCPEvaluatorAgent
from .red_team_a2a_evaluator_agent import RedTeamA2AEvaluatorAgent
from .red_team_mcp_evaluator_agent import RedTeamMCPEvaluatorAgent

_PROTOCOL_TO_AGENT_CLASS = {
    Protocol.A2A: A2AEvaluatorAgent,
    Protocol.MCP: MCPEvaluatorAgent,
}

_PROTOCOL_TO_RED_TEAM_AGENT_CLASS = {
    Protocol.A2A: RedTeamA2AEvaluatorAgent,
    Protocol.MCP: RedTeamMCPEvaluatorAgent,
}


def get_evaluator_agent(
    protocol: Protocol,
    transport: Transport | None,
    evaluated_agent_address: str,
    judge_llm: str,
    scenarios: Scenarios,
    business_context: Optional[str],
    headers: Optional[dict[str, str]] = None,
    judge_llm_auth: Optional[str] = None,
    judge_llm_aws_access_key_id: Optional[str] = None,
    judge_llm_aws_secret_access_key: Optional[str] = None,
    judge_llm_aws_region: Optional[str] = None,
    debug: bool = False,
    deep_test_mode: bool = False,
    chat_update_callback: Optional[Callable[[dict], None]] = None,
    evaluation_mode: EvaluationMode = EvaluationMode.POLICY,
    owasp_categories: Optional[List[str]] = None,
    **kwargs,
) -> BaseEvaluatorAgent:
    """
    Get an evaluator agent based on protocol and evaluation mode.

    Args:
        protocol: Communication protocol (A2A or MCP)
        transport: Transport mechanism
        evaluated_agent_address: URL of the agent to evaluate
        judge_llm: LLM to use for evaluation
        scenarios: Scenarios to test
        business_context: Business context for the target agent
        headers: HTTP headers for agent connection
        judge_llm_auth: API key for judge LLM
        judge_llm_aws_access_key_id: AWS access key ID for judge LLM
        judge_llm_aws_secret_access_key: AWS secret access key for judge LLM
        judge_llm_aws_region: AWS region for judge LLM
        debug: Enable debug logging
        deep_test_mode: Enable deep testing mode
        chat_update_callback: Callback for chat updates
        evaluation_mode: Evaluation mode (POLICY or RED_TEAM)
        owasp_categories: List of OWASP category IDs for red team mode
        **kwargs: Additional keyword arguments

    Returns:
        BaseEvaluatorAgent instance
    """
    # Select agent class based on protocol and evaluation mode
    if evaluation_mode == EvaluationMode.RED_TEAM:
        agent_class = _PROTOCOL_TO_RED_TEAM_AGENT_CLASS.get(protocol, None)
        if not agent_class:
            raise ValueError(
                f"Invalid protocol for red team mode: {protocol}",
            )

        # Red team agents require owasp_categories
        if not owasp_categories:
            raise ValueError(
                "owasp_categories must be provided for red team evaluation mode",
            )

        return agent_class(
            transport=transport,
            evaluated_agent_address=evaluated_agent_address,
            judge_llm=judge_llm,
            scenarios=scenarios,
            business_context=business_context,
            headers=headers,
            judge_llm_auth=judge_llm_auth,
            debug=debug,
            chat_update_callback=chat_update_callback,
            owasp_categories=owasp_categories,
            **kwargs,
        )
    else:
        # Policy mode (default)
        agent_class = _PROTOCOL_TO_AGENT_CLASS.get(protocol, None)
        if not agent_class:
            raise ValueError(f"Invalid protocol: {protocol}")

        return agent_class(
            transport=transport,
            evaluated_agent_address=evaluated_agent_address,
            judge_llm=judge_llm,
            scenarios=scenarios,
            business_context=business_context,
            headers=headers,
            judge_llm_auth=judge_llm_auth,
            judge_llm_aws_access_key_id=judge_llm_aws_access_key_id,
            judge_llm_aws_secret_access_key=judge_llm_aws_secret_access_key,
            judge_llm_aws_region=judge_llm_aws_region,
            debug=debug,
            deep_test_mode=deep_test_mode,
            chat_update_callback=chat_update_callback,
            **kwargs,
        )
