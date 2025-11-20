"""
Single-turn attack techniques.

These attacks transform a single input message to bypass security measures.
"""

from .base64 import Base64
from .base_single_turn_attack import BaseSingleTurnAttack
from .leetspeak import Leetspeak
from .prompt_injection import PromptInjection
from .prompt_probing import PromptProbing
from .roleplay import Roleplay
from .rot13 import ROT13

__all__ = [
    "BaseSingleTurnAttack",
    "PromptInjection",
    "PromptProbing",
    "Base64",
    "ROT13",
    "Leetspeak",
    "Roleplay",
]
