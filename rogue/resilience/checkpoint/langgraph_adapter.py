"""
LangGraph checkpoint adapter for resilience recovery testing.

Requires LangGraph to be installed (``uv sync --group examples``).
"""

from typing import Any, Optional

from rogue.common.logging import get_logger

from .base import (
    CheckpointAdapter,
    CheckpointError,
    CheckpointInfo,
    CheckpointNotFoundError,
    CheckpointRestoreError,
    CheckpointSnapshot,
)

logger = get_logger(__name__)


class LangGraphCheckpointAdapter(CheckpointAdapter):
    """
    Checkpoint adapter backed by a LangGraph ``CompiledStateGraph``.

    Bridges LangGraph's checkpointer API (``MemorySaver``, ``SqliteSaver``, etc.)
    to the resilience orchestrator's recovery flow. Typical usage:

    1. Run a baseline graph invocation to create checkpoint ``C0``
    2. Call ``snapshot(thread_id)`` before fault injection
    3. After injector teardown, call ``restore(thread_id, C0)`` to rewind state
    4. Re-run recovery validation against the restored checkpoint

    The adapter validates inputs, wraps LangGraph errors in ``CheckpointError``
    subclasses, and logs each operation for experiment traceability.

    Args:
        graph: Compiled LangGraph state graph with a checkpointer attached.
        checkpointer: Optional explicit checkpointer; defaults to
            ``graph.checkpointer`` when omitted.

    Raises:
        ValueError: If the graph has no checkpointer configured.
    """

    def __init__(self, graph: Any, checkpointer: Optional[Any] = None) -> None:
        if graph is None:
            raise ValueError("LangGraphCheckpointAdapter requires a compiled graph")
        self._graph = graph
        self._checkpointer = checkpointer or getattr(graph, "checkpointer", None)
        if self._checkpointer is None:
            raise ValueError(
                "LangGraphCheckpointAdapter requires a graph with a checkpointer. "
                "Compile the graph with checkpointer=MemorySaver() or SqliteSaver(...).",
            )

    def _validate_thread_id(self, thread_id: str) -> None:
        """Ensure thread_id is a non-empty string."""
        if not thread_id or not str(thread_id).strip():
            raise ValueError("thread_id must be a non-empty string")

    def _validate_checkpoint_id(self, checkpoint_id: str) -> None:
        """Ensure checkpoint_id is present before restore operations."""
        if not checkpoint_id or not str(checkpoint_id).strip():
            raise ValueError("checkpoint_id must be a non-empty string")

    def _config(self, thread_id: str, checkpoint_id: Optional[str] = None) -> dict:
        """
        Build a LangGraph runnable config for the given thread/checkpoint.

        Args:
            thread_id: LangGraph thread identifier.
            checkpoint_id: Optional checkpoint to address directly.

        Returns:
            Config dict suitable for ``get_state``, ``invoke``, etc.
        """
        self._validate_thread_id(thread_id)
        configurable: dict[str, str] = {"thread_id": thread_id}
        if checkpoint_id is not None:
            self._validate_checkpoint_id(checkpoint_id)
            configurable["checkpoint_id"] = checkpoint_id
        return {"configurable": configurable}

    def snapshot(self, thread_id: str) -> CheckpointSnapshot:
        """
        Capture the latest checkpoint for a LangGraph thread.

        Invokes ``graph.get_state`` and extracts the checkpoint ID and state
        values. The graph must have been invoked at least once for the thread
        before a snapshot can be taken.

        Args:
            thread_id: LangGraph ``thread_id`` in runnable config.

        Returns:
            Snapshot with checkpoint ID and serialized state values.

        Raises:
            ValueError: If ``thread_id`` is empty.
            CheckpointNotFoundError: If no checkpoint exists for the thread.
            CheckpointError: If LangGraph state retrieval fails unexpectedly.
        """
        try:
            state = self._graph.get_state(self._config(thread_id))
        except Exception as exc:
            logger.exception(
                "LangGraph get_state failed during snapshot",
                extra={"thread_id": thread_id},
            )
            raise CheckpointError(
                f"Failed to read LangGraph state for thread {thread_id}: {exc}",
            ) from exc

        configurable = state.config.get("configurable", {})
        checkpoint_id = configurable.get("checkpoint_id", "")
        if not checkpoint_id:
            raise CheckpointNotFoundError(
                f"No checkpoint available for thread {thread_id!r}. "
                "Invoke the graph at least once before snapshotting.",
            )

        values = state.values if isinstance(state.values, dict) else {}
        logger.info(
            "Captured LangGraph checkpoint",
            extra={"thread_id": thread_id, "checkpoint_id": checkpoint_id},
        )
        return CheckpointSnapshot(
            thread_id=thread_id,
            checkpoint_id=checkpoint_id,
            state_values=values,
            metadata={"next": list(state.next or [])},
        )

    def restore(self, thread_id: str, checkpoint_id: str) -> None:
        """
        Restore LangGraph state to a prior checkpoint.

        Reads state at ``checkpoint_id`` and writes it back via
        ``graph.update_state``, creating a new checkpoint that reflects the
        pre-fault state.

        Args:
            thread_id: LangGraph thread identifier.
            checkpoint_id: Checkpoint ID returned from ``snapshot()``.

        Raises:
            ValueError: If ``thread_id`` or ``checkpoint_id`` is empty.
            NotImplementedError: If the graph lacks ``update_state``.
            CheckpointNotFoundError: If the target checkpoint cannot be read.
            CheckpointRestoreError: If the restore write fails.
        """
        self._validate_thread_id(thread_id)
        self._validate_checkpoint_id(checkpoint_id)

        if not hasattr(self._graph, "update_state"):
            raise NotImplementedError(
                "Graph does not support update_state; cannot restore checkpoint",
            )

        try:
            target_state = self._graph.get_state(self._config(thread_id, checkpoint_id))
        except Exception as exc:
            logger.exception(
                "LangGraph get_state failed during restore",
                extra={"thread_id": thread_id, "checkpoint_id": checkpoint_id},
            )
            raise CheckpointNotFoundError(
                f"Checkpoint {checkpoint_id!r} not found for thread {thread_id!r}: {exc}",
            ) from exc

        values = target_state.values if isinstance(target_state.values, dict) else {}
        try:
            self._graph.update_state(self._config(thread_id), values)
        except Exception as exc:
            logger.exception(
                "LangGraph update_state failed during restore",
                extra={"thread_id": thread_id, "checkpoint_id": checkpoint_id},
            )
            raise CheckpointRestoreError(
                f"Failed to restore checkpoint {checkpoint_id!r} "
                f"for thread {thread_id!r}: {exc}",
            ) from exc

        logger.info(
            "Restored LangGraph checkpoint",
            extra={"thread_id": thread_id, "checkpoint_id": checkpoint_id},
        )

    def list_checkpoints(self, thread_id: str) -> list[CheckpointInfo]:
        """
        List checkpoint history for a LangGraph thread.

        Uses ``get_state_history`` when available; otherwise returns a
        single-entry list from the current state.

        Args:
            thread_id: LangGraph thread identifier.

        Returns:
            Checkpoints ordered from oldest to newest.

        Raises:
            ValueError: If ``thread_id`` is empty.
            CheckpointError: If LangGraph history retrieval fails.
        """
        self._validate_thread_id(thread_id)

        if not hasattr(self._graph, "get_state_history"):
            try:
                state = self._graph.get_state(self._config(thread_id))
            except Exception as exc:
                raise CheckpointError(
                    f"Failed to list checkpoints for thread {thread_id}: {exc}",
                ) from exc
            checkpoint_id = state.config.get("configurable", {}).get("checkpoint_id", "")
            if not checkpoint_id:
                return []
            return [CheckpointInfo(checkpoint_id=checkpoint_id, thread_id=thread_id)]

        try:
            infos: list[CheckpointInfo] = []
            for snapshot in self._graph.get_state_history(self._config(thread_id)):
                checkpoint_id = snapshot.config.get("configurable", {}).get(
                    "checkpoint_id",
                    "",
                )
                if checkpoint_id:
                    infos.append(
                        CheckpointInfo(
                            checkpoint_id=checkpoint_id,
                            thread_id=thread_id,
                            metadata={"next": list(snapshot.next or [])},
                        ),
                    )
            return list(reversed(infos))
        except Exception as exc:
            logger.exception(
                "LangGraph get_state_history failed",
                extra={"thread_id": thread_id},
            )
            raise CheckpointError(
                f"Failed to list checkpoint history for thread {thread_id}: {exc}",
            ) from exc

    def supports_replay(self) -> bool:
        """
        Whether checkpoint history replay is available.

        Returns:
            True when the graph exposes ``get_state_history``.
        """
        return hasattr(self._graph, "get_state_history")
