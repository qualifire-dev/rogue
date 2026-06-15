"""Tests for LangGraph checkpoint adapter (optional dependency)."""

import pytest

pytest.importorskip("langgraph")

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.graph import END, START, StateGraph  # noqa: E402
from typing import TypedDict  # noqa: E402

from rogue.resilience.checkpoint.base import CheckpointNotFoundError  # noqa: E402
from rogue.resilience.checkpoint.langgraph_adapter import LangGraphCheckpointAdapter  # noqa: E402


class _State(TypedDict):
    counter: int


def _inc(state: _State) -> dict:
    return {"counter": state.get("counter", 0) + 1}


@pytest.fixture
def graph():
    builder = StateGraph(_State)
    builder.add_node("inc", _inc)
    builder.add_edge(START, "inc")
    builder.add_edge("inc", END)
    return builder.compile(checkpointer=MemorySaver())


def test_snapshot_and_list_checkpoints(graph) -> None:
    thread_id = "test-thread"
    graph.invoke({"counter": 0}, {"configurable": {"thread_id": thread_id}})
    adapter = LangGraphCheckpointAdapter(graph)
    snapshot = adapter.snapshot(thread_id)
    assert snapshot.checkpoint_id
    checkpoints = adapter.list_checkpoints(thread_id)
    assert len(checkpoints) >= 1


def test_restore_checkpoint(graph) -> None:
    thread_id = "restore-thread"
    graph.invoke({"counter": 0}, {"configurable": {"thread_id": thread_id}})
    adapter = LangGraphCheckpointAdapter(graph)
    snapshot = adapter.snapshot(thread_id)
    graph.invoke({"counter": 0}, {"configurable": {"thread_id": thread_id}})
    adapter.restore(thread_id, snapshot.checkpoint_id)
    state = graph.get_state({"configurable": {"thread_id": thread_id}})
    assert state.values.get("counter", 0) >= 1


def test_snapshot_requires_invoke(graph) -> None:
    adapter = LangGraphCheckpointAdapter(graph)
    with pytest.raises(CheckpointNotFoundError):
        adapter.snapshot("never-invoked-thread")


def test_restore_rejects_empty_checkpoint_id(graph) -> None:
    adapter = LangGraphCheckpointAdapter(graph)
    thread_id = "test-thread"
    graph.invoke({"counter": 0}, {"configurable": {"thread_id": thread_id}})
    with pytest.raises(ValueError):
        adapter.restore(thread_id, "")
