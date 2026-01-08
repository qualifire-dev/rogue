"""
Base64 encoding attack technique.

Encodes the attack input in Base64 to bypass text-based filters.
"""

import base64

from .base_single_turn_attack import BaseSingleTurnAttack


class Base64(BaseSingleTurnAttack):
    """Base64 encoding attack."""

    name = "Base64"

    def __init__(self, weight: int = 1):
        self.weight = weight

    def enhance(self, attack: str) -> str:
        """Enhance the attack using Base64 encoding."""
        return base64.b64encode(attack.encode()).decode()

    async def a_enhance(self, attack: str) -> str:
        """Async version of enhance."""
        return self.enhance(attack)

    def get_name(self) -> str:
        return self.name
