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