"""
Premium injector catalog for Rogue Resilience.

Mirrors the Red Team ``PREMIUM_*_ATTACKS`` pattern: local premium injectors
ship in-repo; Deckard-hosted probes require ``ROGUE_SECURITY_API_KEY``.
"""

from dataclasses import dataclass
from typing import Dict, List

from .gradual_goal_drift import GradualGoalDriftInjector


@dataclass(frozen=True)
class PremiumInjectorMeta:
    """Metadata for a premium resilience injector."""

    id: str
    name: str
    description: str
    deckard_required: bool = False


PREMIUM_INJECTOR_METADATA: Dict[str, PremiumInjectorMeta] = {
    "gradual_goal_drift": PremiumInjectorMeta(
        id="gradual_goal_drift",
        name="Gradual Goal Drift",
        description="Multi-turn sub-goal escalation before overt rogue behavior",
        deckard_required=False,
    ),
    "deckard_adaptive_injection": PremiumInjectorMeta(
        id="deckard_adaptive_injection",
        name="Deckard Adaptive Injection",
        description="Cloud-generated probes tailored to business context via Rogue Security",
        deckard_required=True,
    ),
}

PREMIUM_INJECTOR_CLASSES = {
    "gradual_goal_drift": GradualGoalDriftInjector,
}


def list_premium_injectors() -> List[PremiumInjectorMeta]:
    """Return premium injector metadata for API and UI catalogs."""
    return list(PREMIUM_INJECTOR_METADATA.values())
