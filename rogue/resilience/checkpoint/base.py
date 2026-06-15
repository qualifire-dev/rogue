"""
Checkpoint adapter base classes for resilience recovery testing.

Checkpoint adapters are optional and require LangGraph (``uv sync --group
examples`` or the ``resilience`` dependency group).
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class CheckpointError(Exception):
    """Base exception for checkpoint adapter failures."""


class CheckpointNotFoundError(CheckpointError):
    """Raised when a requested checkpoint or thread does not exist."""


class CheckpointRestoreError(CheckpointError):
    """Raised when restoring a checkpoint fails."""


class CheckpointInfo(BaseModel):
    """Metadata for a single checkpoint in a thread history."""

    checkpoint_id: str
    thread_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class CheckpointSnapshot(BaseModel):
    """Captured checkpoint state before fault injection."""

    thread_id: str
    checkpoint_id: str
    state_values: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CheckpointAdapter(ABC):
    """Abstract adapter bridging orchestrator recovery to a checkpoint backend."""

    @abstractmethod
    def snapshot(self, thread_id: str) -> CheckpointSnapshot:
        """Capture the latest checkpoint for a thread."""

    @abstractmethod
    def restore(self, thread_id: str, checkpoint_id: str) -> None:
        """Restore thread state to a prior checkpoint."""

    @abstractmethod
    def list_checkpoints(self, thread_id: str) -> list[CheckpointInfo]:
        """List checkpoint history for a thread."""

    def supports_replay(self) -> bool:
        """Return True when full checkpoint history replay is available."""
        return False
