"""
Python entrypoint for hierarchical multi-agent resilience experiments.

Usage:
    uv run python -m examples.multi_agent_hierarchical.run_resilience_demo
"""

from typing import Any, Optional

from .agents import route_agent


def call_agent(
    messages: list[dict[str, Any]],
    context_id: Optional[str] = None,
    agent_id: str = "supervisor",
    **kwargs: Any,
) -> str:
    """
    Route a message to a specific agent in the hierarchical system.

    Args:
        messages: OpenAI-style conversation history.
        context_id: Session identifier provided by Rogue.
        agent_id: Target agent (supervisor, worker-1, worker-2).
        **kwargs: Injector side-data forwarded on fault probes.

    Returns:
        Agent response string.
    """
    return route_agent(agent_id, messages, **kwargs)
