"""Checkpoint adapters for resilience recovery testing."""

from .base import (
    CheckpointAdapter,
    CheckpointError,
    CheckpointInfo,
    CheckpointNotFoundError,
    CheckpointRestoreError,
    CheckpointSnapshot,
)


def get_langgraph_checkpoint_adapter(graph: object, checkpointer: object | None = None):
    """
    Factory for ``LangGraphCheckpointAdapter`` with optional dependency guard.

    Args:
        graph: Compiled LangGraph state graph.
        checkpointer: Optional explicit checkpointer instance.

    Returns:
        Configured ``LangGraphCheckpointAdapter``.

    Raises:
        ImportError: If LangGraph is not installed.
        ValueError: If the graph has no checkpointer.
    """
    try:
        from .langgraph_adapter import LangGraphCheckpointAdapter
    except ImportError as exc:
        raise ImportError(
            "LangGraph is required for checkpoint adapters. "
            "Install with: uv sync --group examples",
        ) from exc
    return LangGraphCheckpointAdapter(graph, checkpointer=checkpointer)


__all__ = [
    "CheckpointAdapter",
    "CheckpointError",
    "CheckpointInfo",
    "CheckpointNotFoundError",
    "CheckpointRestoreError",
    "CheckpointSnapshot",
    "get_langgraph_checkpoint_adapter",
]
