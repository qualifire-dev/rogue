from typing import Callable, Optional

from rogue_sdk.types import Protocol, Scenarios, Transport

from .a2a.a2a_evaluator_agent import A2AEvaluatorAgent
from .base_evaluator_agent import BaseEvaluatorAgent
from .mcp.mcp_evaluator_agent import MCPEvaluatorAgent

_PROTOCOOL_TO_AGENT_CLASS = {
    Protocol.A2A: A2AEvaluatorAgent,
    Protocol.MCP: MCPEvaluatorAgent,
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
    debug: bool = False,
    deep_test_mode: bool = False,
    chat_update_callback: Optional[Callable[[dict], None]] = None,
    **kwargs,
) -> BaseEvaluatorAgent:
    agent_class = _PROTOCOOL_TO_AGENT_CLASS.get(protocol, None)
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
        debug=debug,
        deep_test_mode=deep_test_mode,
        chat_update_callback=chat_update_callback,
        **kwargs,
    )
