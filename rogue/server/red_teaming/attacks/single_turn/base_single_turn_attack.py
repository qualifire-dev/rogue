"""
Base class for single-turn attacks.

Single-turn attacks transform a single input message to bypass security measures.
"""

from ..base_attack import BaseAttack


class BaseSingleTurnAttack(BaseAttack):
    """Base class for attacks that transform a single input."""

    multi_turn: bool = False
