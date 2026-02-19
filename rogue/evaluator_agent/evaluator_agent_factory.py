"""
Evaluator Agent Factory.

Creates the appropriate evaluator agent based on protocol.
Policy evaluation uses these agents, while red team evaluation
is handled by the server's red_teaming.orchestrator module.
"""

from typing import Callable, Optional

from rogue_sdk.types import Protocol, Scenarios, Transport

from .a2a.a2a_evaluator_agent import A2AEvaluatorAgent
from .base_evaluator_agent import BaseEvaluatorAgent
from .mcp.mcp_evaluator_agent import MCPEvaluatorAgent
from .openai_api.openai_api_evaluator_agent import OpenAIAPIEvaluatorAgent
from .python.python_evaluator_agent import PythonEvaluatorAgent

_PROTOCOL_TO_AGENT_CLASS = {
    Protocol.A2A: A2AEvaluatorAgent,
    Protocol.MCP: MCPEvaluatorAgent,
    Protocol.PYTHON: PythonEvaluatorAgent,
    Protocol.OPENAI_API: OpenAIAPIEvaluatorAgent,
}


def get_evaluator_agent(
    protocol: Protocol,
    transport: Optional[Transport],
    evaluated_agent_address: Optional[str] = None,
    judge_llm: str = "",
    scenarios: Optional[Scenarios] = None,
    business_context: Optional[str] = None,
    headers: Optional[dict[str, str]] = None,
    judge_llm_auth: Optional[str] = None,
    judge_llm_aws_access_key_id: Optional[str] = None,
    judge_llm_aws_secret_access_key: Optional[str] = None,
    judge_llm_aws_region: Optional[str] = None,
    debug: bool = False,
    deep_test_mode: bool = False,
    chat_update_callback: Optional[Callable[[dict], None]] = None,
    python_entrypoint_file: Optional[str] = None,
    **kwargs,
) -> BaseEvaluatorAgent:
    """
    Get an evaluator agent based on protocol.

    This factory creates agents for policy-based scenario evaluation.
    Red team (vulnerability-centric) evaluation is handled separately
    by the server's red_teaming.orchestrator module.

    Args:
        protocol: Communication protocol (A2A, MCP, PYTHON, or OPENAI_API)
        transport: Transport mechanism (not used for PYTHON protocol)
        evaluated_agent_address: URL of the agent to evaluate (for A2A/MCP/OPENAI_API)
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
        python_entrypoint_file: Path to Python file with call_agent function
            (required for PYTHON protocol)
        **kwargs: Additional keyword arguments

    Returns:
        BaseEvaluatorAgent instance
    """
    agent_class = _PROTOCOL_TO_AGENT_CLASS.get(protocol, None)
    if not agent_class:
        raise ValueError(f"Invalid protocol: {protocol}")

    # Handle Python protocol specially
    if protocol == Protocol.PYTHON:
        from loguru import logger

        logger.debug(
            f"🐍 Factory received python_entrypoint_file: {python_entrypoint_file!r}",
        )
        if not python_entrypoint_file:
            raise ValueError(
                "python_entrypoint_file is required for PYTHON protocol",
            )
        return PythonEvaluatorAgent(
            python_file_path=python_entrypoint_file,
            judge_llm=judge_llm,
            scenarios=scenarios or Scenarios(),
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

    # Handle A2A, MCP, and OPENAI_API protocols
    if not evaluated_agent_address:
        raise ValueError(
            f"evaluated_agent_address is required for {protocol.value} protocol",
        )

    return agent_class(
        transport=transport,
        evaluated_agent_address=evaluated_agent_address,
        judge_llm=judge_llm,
        scenarios=scenarios or Scenarios(),
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
