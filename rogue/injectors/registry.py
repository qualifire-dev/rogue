"""
Injector registry for Rogue Resilience fault injection strategies.

Mirrors the catalog pattern used by ``server/red_teaming/catalog/attacks.py``.
Supports built-in ``InjectorId`` strategies, premium injectors, and custom plugins.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Type, Union

from rogue.common.logging import get_logger

from .action_spam import ActionSpamInjector
from .base_injector import BaseInjector, InjectorId
from .goal_conflict import GoalConflictInjector
from .gradual_goal_drift import GradualGoalDriftInjector
from .hallucination_spamming import HallucinationSpammingInjector
from .policy_violation import PolicyViolationInjector
from .premium_catalog import PREMIUM_INJECTOR_CLASSES
from .tool_misuse import ToolMisuseInjector

logger = get_logger(__name__)

InjectorKey = Union[InjectorId, str]


@dataclass(frozen=True)
class InjectorDefinition:
    """
    Catalog entry describing a registered injector.

    Attributes:
        id: Stable injector identifier (enum value or custom string).
        name: Human-readable display name.
        description: Short explanation of the strategy.
        factory: Callable that returns a fresh injector instance.
        premium: Whether Rogue Security / Deckard is required.
        custom: True for plugin-registered injectors.
    """

    id: InjectorKey
    name: str
    description: str
    factory: Callable[[], BaseInjector]
    premium: bool = False
    custom: bool = False


_BUILTIN_CLASSES: Dict[InjectorId, Type[BaseInjector]] = {
    InjectorId.TOOL_MISUSE: ToolMisuseInjector,
    InjectorId.HALLUCINATION_SPAMMING: HallucinationSpammingInjector,
    InjectorId.GOAL_CONFLICT: GoalConflictInjector,
    InjectorId.POLICY_VIOLATION: PolicyViolationInjector,
    InjectorId.ACTION_SPAM: ActionSpamInjector,
}

_PREMIUM_BUILTIN: Dict[str, Type[BaseInjector]] = {
    **{k: v for k, v in PREMIUM_INJECTOR_CLASSES.items()},
    "gradual_goal_drift": GradualGoalDriftInjector,
}

_CUSTOM_CATALOG: Dict[str, InjectorDefinition] = {}


def _built_in_definition(injector_id: InjectorId, cls: Type[BaseInjector]) -> InjectorDefinition:
    return InjectorDefinition(
        id=injector_id,
        name=cls.name,
        description=cls.description,
        factory=cls,
        premium=getattr(cls, "premium", False),
        custom=False,
    )


INJECTOR_CATALOG: Dict[InjectorKey, InjectorDefinition] = {
    injector_id: _built_in_definition(injector_id, cls)
    for injector_id, cls in _BUILTIN_CLASSES.items()
}

for premium_id, cls in _PREMIUM_BUILTIN.items():
    INJECTOR_CATALOG[premium_id] = InjectorDefinition(
        id=premium_id,
        name=cls.name,
        description=cls.description,
        factory=cls,
        premium=True,
        custom=False,
    )


def register_injector_definition(definition: InjectorDefinition) -> None:
    """Register or replace a catalog entry (used by plugin loader)."""
    key = definition.id.value if isinstance(definition.id, InjectorId) else str(definition.id)
    _CUSTOM_CATALOG[key] = definition
    INJECTOR_CATALOG[key] = definition
    logger.info("Injector registered", extra={"id": key, "custom": definition.custom})


def _resolve_key(injector_id: InjectorKey) -> str:
    if isinstance(injector_id, InjectorId):
        return injector_id.value
    return str(injector_id)


def get_injector(injector_id: InjectorKey) -> BaseInjector:
    """
    Instantiate an injector by ID.

    Args:
        injector_id: Built-in enum, premium string, or custom plugin ID.

    Returns:
        A fresh, unconfigured injector instance.

    Raises:
        KeyError: If the injector ID is not registered in the catalog.
    """
    key = _resolve_key(injector_id)
    if key not in INJECTOR_CATALOG:
        # Try enum coercion for backward compatibility
        try:
            enum_id = InjectorId(key)
            key = enum_id.value
        except ValueError as exc:
            logger.error("Unknown injector requested", extra={"id": key})
            raise KeyError(f"Unknown injector: {key}") from exc

    definition = INJECTOR_CATALOG.get(key)
    if definition is None:
        logger.error("Unknown injector requested", extra={"id": key})
        raise KeyError(f"Unknown injector: {key}")
    return definition.factory()


def list_injectors(*, include_premium: bool = True) -> List[InjectorDefinition]:
    """
    Return registered injector definitions.

    Args:
        include_premium: When False, omit premium strategies from the list.

    Returns:
        List of catalog entries.
    """
    entries = list(INJECTOR_CATALOG.values())
    if not include_premium:
        entries = [e for e in entries if not e.premium]
    return entries


def is_premium_injector(injector_id: InjectorKey) -> bool:
    """Return True if the injector requires Rogue Security / Deckard."""
    key = _resolve_key(injector_id)
    definition = INJECTOR_CATALOG.get(key)
    return bool(definition and definition.premium)
