"""
Injector registry for Rogue Resilience fault injection strategies.

Mirrors the catalog pattern used by ``server/red_teaming/catalog/attacks.py``.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Type

from rogue.common.logging import get_logger

from .action_spam import ActionSpamInjector
from .base_injector import BaseInjector, InjectorId
from .goal_conflict import GoalConflictInjector
from .hallucination_spamming import HallucinationSpammingInjector
from .policy_violation import PolicyViolationInjector
from .tool_misuse import ToolMisuseInjector

logger = get_logger(__name__)


@dataclass(frozen=True)
class InjectorDefinition:
    """
    Catalog entry describing a registered injector.

    Attributes:
        id: Stable injector identifier.
        name: Human-readable display name.
        description: Short explanation of the strategy.
        factory: Callable that returns a fresh injector instance.
    """

    id: InjectorId
    name: str
    description: str
    factory: Callable[[], BaseInjector]


_INJECTOR_CLASSES: Dict[InjectorId, Type[BaseInjector]] = {
    InjectorId.TOOL_MISUSE: ToolMisuseInjector,
    InjectorId.HALLUCINATION_SPAMMING: HallucinationSpammingInjector,
    InjectorId.GOAL_CONFLICT: GoalConflictInjector,
    InjectorId.POLICY_VIOLATION: PolicyViolationInjector,
    InjectorId.ACTION_SPAM: ActionSpamInjector,
}


INJECTOR_CATALOG: Dict[InjectorId, InjectorDefinition] = {
    injector_id: InjectorDefinition(
        id=injector_id,
        name=cls.name,
        description=cls.description,
        factory=cls,
    )
    for injector_id, cls in _INJECTOR_CLASSES.items()
}


def get_injector(injector_id: InjectorId | str) -> BaseInjector:
    """
    Instantiate an injector by ID.

    Args:
        injector_id: Registered injector identifier (enum or string value).

    Returns:
        A fresh, unconfigured injector instance.

    Raises:
        ValueError: If ``injector_id`` is not a valid ``InjectorId`` value.
        KeyError: If the injector ID is not registered in the catalog.
    """
    if isinstance(injector_id, str):
        try:
            injector_id = InjectorId(injector_id)
        except ValueError as exc:
            logger.error("Invalid injector ID requested", extra={"id": injector_id})
            raise ValueError(f"Invalid injector ID: {injector_id}") from exc

    definition = INJECTOR_CATALOG.get(injector_id)
    if definition is None:
        logger.error("Unknown injector requested", extra={"id": injector_id.value})
        raise KeyError(f"Unknown injector: {injector_id}")
    return definition.factory()


def list_injectors() -> List[InjectorDefinition]:
    """
    Return all registered injector definitions.

    Returns:
        List of catalog entries, one per built-in injector strategy.
    """
    return list(INJECTOR_CATALOG.values())
