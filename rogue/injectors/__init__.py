"""Fault injection strategies for Rogue Resilience experiments."""

from .base_injector import (
    BaseInjector,
    InjectionContext,
    InjectionResult,
    InjectorConfig,
    InjectorId,
)
from .registry import INJECTOR_CATALOG, get_injector, list_injectors
from .plugins import load_injector_plugin, register_injector

__all__ = [
    "BaseInjector",
    "InjectionContext",
    "InjectionResult",
    "InjectorConfig",
    "InjectorId",
    "INJECTOR_CATALOG",
    "get_injector",
    "list_injectors",
    "load_injector_plugin",
    "register_injector",
]
