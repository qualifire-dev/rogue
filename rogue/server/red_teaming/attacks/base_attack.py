"""
Base attack class for red teaming attacks.

Adapted from deepteam/attacks/base_attack.py for Rogue's architecture.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from rogue.server.red_teaming.strategy_metadata import (
    StrategyMetadata,
    get_strategy_metadata,
)


class BaseAttack(ABC):
    """
    Base class for all red teaming attacks.

    Attacks can be single-turn (transform a single input) or multi-turn
    (guide a conversation strategy). Attacks are weighted for random sampling
    during scenario generation.

    Attributes:
        weight: Sampling weight for attack selection (higher = more likely)
        multi_turn: Whether this is a multi-turn attack strategy
        name: Human-readable name of the attack
        requires_llm_agent: Whether this attack requires an LLM agent
            (for agentic strategies)
    """

    weight: int = 1
    multi_turn: bool = False
    name: str
    # True for advanced agentic strategies (Hydra, GOAT, etc.)
    requires_llm_agent: bool = False

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

    def get_system_instructions(self) -> Optional[str]:
        """
        Get system instructions for the Red Team Agent.
        Used primarily by multi-turn strategies to guide the agent's behavior.
        """
        return None

    def get_conversation_plan(self) -> Optional[List[str]]:
        """
        Get a structured plan for the conversation.
        """
        return None

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this attack technique."""
        raise NotImplementedError("Subclasses must implement get_name()")

    def get_strategy_id(self) -> str:
        """
        Get the strategy ID for this attack.

        By default, uses the lowercase attack name. Subclasses can override
        to provide more specific strategy identifiers.

        Returns:
            Strategy ID string used for metadata lookup
        """
        return self.get_name().lower().replace(" ", "_").replace("-", "_")

    def get_metadata(self) -> StrategyMetadata:
        """
        Get strategy metadata for this attack.

        Metadata includes human exploitability, complexity level,
        and description. Used for risk scoring and reporting.

        Returns:
            StrategyMetadata object with attack characteristics
        """
        return get_strategy_metadata(self.get_strategy_id())
