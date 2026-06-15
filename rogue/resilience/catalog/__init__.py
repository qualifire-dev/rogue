"""Architecture profile catalog for multi-agent resilience testing."""

from .architectures import (
    ARCHITECTURE_CATALOG,
    AgentRole,
    ArchitectureProfile,
    get_architecture,
    list_architectures,
)

__all__ = [
    "ARCHITECTURE_CATALOG",
    "AgentRole",
    "ArchitectureProfile",
    "get_architecture",
    "list_architectures",
]
