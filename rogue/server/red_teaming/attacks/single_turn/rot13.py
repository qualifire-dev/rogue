"""
ROT13 encoding attack technique.

Encodes the attack input using ROT13 cipher to bypass text-based filters.
"""

from .base_single_turn_attack import BaseSingleTurnAttack


class ROT13(BaseSingleTurnAttack):
    """ROT13 encoding attack."""

    name = "ROT-13"

    def __init__(self, weight: int = 1):
        self.weight = weight

    def enhance(self, attack: str) -> str:
        """Enhance the attack using ROT13 encoding."""
        return attack.translate(
            str.maketrans(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
            ),
        )

    async def a_enhance(self, attack: str) -> str:
        """Async version of enhance."""
        return self.enhance(attack)

    def get_name(self) -> str:
        return self.name
