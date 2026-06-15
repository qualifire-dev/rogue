"""
Minimal LangGraph agent with checkpoint support for recovery demos.

Uses a deterministic state graph (no LLM required) so the example runs in CI.
"""

from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph


class AgentState(TypedDict):
    """Simple state tracked across LangGraph checkpoints."""

    messages: list[str]
    counter: int
    healthy: bool


def _process(state: AgentState) -> dict[str, Any]:
    messages = list(state.get("messages", []))
    latest = messages[-1] if messages else ""
    counter = int(state.get("counter", 0)) + 1
    healthy = "rogue" not in latest.lower()
    return {"messages": messages, "counter": counter, "healthy": healthy}


def build_graph():
    """Build and compile the demo graph with an in-memory checkpointer."""
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("process", _process)
    graph_builder.add_edge(START, "process")
    graph_builder.add_edge("process", END)
    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory)


_GRAPH = build_graph()


def get_graph():
    """Return the compiled LangGraph used by checkpoint adapters."""
    return _GRAPH
