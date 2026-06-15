"""
Python entrypoint for LangGraph checkpoint recovery resilience experiments.
"""

from typing import Any, Optional

from langchain_core.runnables import RunnableConfig

from .langgraph_agent import get_graph


def call_agent(
    messages: list[dict[str, Any]],
    context_id: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Invoke the LangGraph agent and return the latest response text.

    Args:
        messages: OpenAI-style message list (latest user message is used).
        context_id: LangGraph thread ID for checkpointing.
        **kwargs: Injector metadata; ``resilience_injection`` marks fault probes.

    Returns:
        Response string derived from graph state.
    """
    graph = get_graph()
    thread_id = context_id or "resilience-langgraph-demo"
    latest = messages[-1]["content"] if messages else ""
    if kwargs.get("resilience_injection"):
        latest = f"rogue injection probe: {latest}"

    config = RunnableConfig(configurable={"thread_id": thread_id})
    result = graph.invoke(
        {"messages": [latest], "counter": 0, "healthy": True},
        config,
    )
    if not result.get("healthy", True):
        return "Agent state unhealthy due to rogue probe."
    return f"Processed turn {result.get('counter', 0)}: {latest[:120]}"


def get_checkpoint_adapter():
    """Optional hook for orchestrator checkpoint integration."""
    from rogue.resilience.checkpoint import get_langgraph_checkpoint_adapter

    return get_langgraph_checkpoint_adapter(get_graph())
