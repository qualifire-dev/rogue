"""
Base injector classes for Rogue Resilience fault injection.

Injectors turn a cooperative agent into a temporarily rogue one at a
controlled point in a workflow, enabling chaos-style resilience testing.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class InjectorId(str, Enum):
    """
    Registered fault injection strategy identifiers.

    Each value maps to a concrete ``BaseInjector`` subclass in
    ``rogue/injectors/`` and an entry in ``INJECTOR_CATALOG``.
    """

    TOOL_MISUSE = "tool_misuse"
    HALLUCINATION_SPAMMING = "hallucination_spamming"
    GOAL_CONFLICT = "goal_conflict"
    POLICY_VIOLATION = "policy_violation"
    ACTION_SPAM = "action_spam"


class InjectorConfig(BaseModel):
    """
    Runtime configuration for a fault injector.

    Attributes:
        intensity: Injection strength from 0 (subtle) to 1 (aggressive).
        max_probe_messages: Cap on probe messages sent after arming.
        injection_turn: Conversation turn at which the injector arms.
        extra: Strategy-specific overrides passed through to injectors.
    """

    intensity: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Injection strength from 0 (subtle) to 1 (aggressive)",
    )
    max_probe_messages: int = Field(
        default=3,
        ge=1,
        description="Maximum probe messages to emit after injection",
    )
    injection_turn: int = Field(
        default=1,
        ge=0,
        description="Conversation turn at which to arm the injector",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy-specific configuration overrides",
    )


class InjectionContext(BaseModel):
    """
    Context available to an injector at injection time.

    Attributes:
        target_agent_id: ID of the agent being faulted.
        conversation_turn: Current turn index in the conversation.
        baseline_task: Message or task run before injection.
        business_context: Domain description for context-aware probes.
        session_id: Unique session identifier for the experiment.
        metadata: Arbitrary experiment metadata (tools, roles, etc.).
    """

    target_agent_id: str = "default"
    conversation_turn: int = 0
    baseline_task: str = ""
    business_context: str = ""
    session_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class InjectionResult(BaseModel):
    """
    Outcome of arming and applying a fault injector.

    Attributes:
        injector_id: Strategy that produced this result.
        target_agent_id: Agent that was faulted.
        injected_at: UTC timestamp when injection was armed.
        armed: Whether the injector is actively armed.
        attach_kwargs: Side-data forwarded to ``call_agent`` on injected turns.
        system_prompt_suffix: Optional prompt modifier during injection.
        probe_messages: Messages sent to the target after injection.
        metadata: Strategy-specific diagnostic data.
    """

    injector_id: InjectorId | str
    target_agent_id: str
    injected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    armed: bool = True
    attach_kwargs: dict[str, Any] = Field(
        default_factory=dict,
        description="Side-data forwarded to call_agent on injected turns",
    )
    system_prompt_suffix: str = Field(
        default="",
        description="Optional prompt modifier appended during injection",
    )
    probe_messages: list[str] = Field(
        default_factory=list,
        description="Messages sent to the target after injection",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseInjector(ABC):
    """
    Base class for fault injection strategies.

    Subclasses define how a target agent is pushed into rogue behavior and
    which probe messages exercise that behavior during an experiment.

    Lifecycle:
        1. ``configure()`` — set intensity and turn options
        2. ``inject()`` — arm the injector and return probes/side-data
        3. ``get_probe_messages()`` — list messages for fault probing
        4. ``teardown()`` — disarm after the experiment completes

    Class attributes:
        id: Catalog identifier for this strategy.
        name: Human-readable display name.
        description: Short explanation of what the strategy tests.
    """

    id: InjectorId | str
    name: str
    description: str

    def __init__(self) -> None:
        """Initialize an unarmed injector with no active configuration."""
        self._config: Optional[InjectorConfig] = None
        self._armed: bool = False

    def configure(self, config: InjectorConfig) -> None:
        """
        Apply runtime configuration before an experiment.

        Args:
            config: Injector settings such as intensity and probe limits.
        """
        self._config = config

    @property
    def config(self) -> InjectorConfig:
        """
        Return the active configuration.

        Returns:
            The configured ``InjectorConfig``, or defaults if ``configure()``
            has not been called yet.
        """
        return self._config or InjectorConfig()

    @property
    def is_armed(self) -> bool:
        """
        Whether the injector is currently armed.

        Returns:
            True if ``inject()`` has been called and ``teardown()`` has not.
        """
        return self._armed

    @abstractmethod
    async def inject(
        self,
        target_agent_id: str,
        context: InjectionContext,
    ) -> InjectionResult:
        """
        Arm the injector and produce injection metadata for the experiment.

        Args:
            target_agent_id: ID of the agent being faulted.
            context: Conversation and experiment context.

        Returns:
            InjectionResult describing probes and side-data for injected turns.
        """

    @abstractmethod
    def get_probe_messages(self) -> list[str]:
        """
        Return probe messages emitted after injection.

        Returns:
            Ordered list of user messages that exercise the fault strategy.
            Implementations may tailor content using ``InjectionContext``.
        """

    def teardown(self) -> None:
        """
        Restore normal behavior after an experiment completes.

        Clears armed state and configuration so the injector can be reused
        in a subsequent experiment with fresh settings.
        """
        self._armed = False
        self._config = None

    def _probe_limit(self) -> int:
        """
        Return the maximum number of probe messages for this run.

        Returns:
            ``max_probe_messages`` from the active configuration.
        """
        return self.config.max_probe_messages
