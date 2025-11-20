"""
Base attack class for red teaming attacks.

Adapted from deepteam/attacks/base_attack.py for Rogue's architecture.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseAttack(ABC):
    """
    Base class for all red teaming attacks.

    Attacks can be single-turn (transform a single input) or multi-turn
    (guide a conversation strategy). Attacks are weighted for random sampling
    during scenario generation.
    """

    weight: int = 1
    multi_turn: bool = False
    name: str

    def enhance(self, attack: str, *args: Any, **kwargs: Any) -> str:
        """
        Enhance an attack input with this attack technique.

        Args:
            attack: The base attack input to enhance
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Enhanced attack string
        """
        return attack

    async def a_enhance(self, attack: str, *args: Any, **kwargs: Any) -> str:
        """
        Async version of enhance.

        Args:
            attack: The base attack input to enhance
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Enhanced attack string
        """
        return self.enhance(attack, *args, **kwargs)

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this attack technique."""
        raise NotImplementedError("Subclasses must implement get_name()")
