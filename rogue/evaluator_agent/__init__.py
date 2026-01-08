"""
Evaluator Agent Module.

Provides agents for evaluating AI systems using different protocols (A2A, MCP).
Policy evaluation uses scenario-based testing.
Red team evaluation is handled by the server's red_teaming module.
"""

from . import (
    a2a,
    base_evaluator_agent,
    evaluator_agent_factory,
    mcp,
    policy_evaluation,
    run_evaluator_agent,
)
from .a2a import A2AEvaluatorAgent
from .mcp import MCPEvaluatorAgent

__all__ = [
    "base_evaluator_agent",
    "evaluator_agent_factory",
    "policy_evaluation",
    "run_evaluator_agent",
    "a2a",
    "mcp",
    "A2AEvaluatorAgent",
    "MCPEvaluatorAgent",
]
