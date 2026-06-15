"""
Multi-agent Python client for resilience experiments.

Extends the Phase 1 ``PythonAgentClient`` with ``agent_id`` routing for
multi-agent entrypoints while remaining backward compatible with single-agent
``call_agent(messages, ...)`` signatures.
"""

import asyncio
import inspect
from typing import Any, Optional

from rogue.common.logging import get_logger
from rogue.resilience.agent_client import PythonAgentClient
from rogue.resilience.catalog.architectures import ArchitectureProfile, get_architecture
from rogue.resilience.models import ArchitectureId

logger = get_logger(__name__)


class MultiAgentPythonClient(PythonAgentClient):
    """
    Python protocol client with per-agent routing for multi-agent systems.

    This client extends ``PythonAgentClient`` for Phase 2 architecture profiles
    (hierarchical, peer-to-peer, etc.). At load time it inspects the entrypoint's
    ``call_agent`` signature to detect ``agent_id`` support:

    - **With ``agent_id``:** routes each call to the requested agent using the
      architecture profile's ``entry_agent_id`` as the default target.
    - **Without ``agent_id``:** falls back to Phase 1 single-agent behavior so
      existing entrypoints continue to work unchanged.

    Example entrypoint contract::

        def call_agent(
            messages: list[dict],
            context_id: str | None = None,
            agent_id: str = "supervisor",
            **kwargs,
        ) -> str:
            ...

    Attributes:
        architecture_profile: Resolved topology (agents, routing, detection points).
        supports_multi_agent: Whether the entrypoint accepts ``agent_id``.

    Args:
        python_file_path: Path to the Python entrypoint module.
        architecture: Architecture profile ID for validation and routing defaults.
    """

    def __init__(
        self,
        python_file_path: str,
        architecture: ArchitectureId | str = ArchitectureId.SINGLE_AGENT,
    ) -> None:
        """
        Initialize the multi-agent client without loading the entrypoint yet.

        Args:
            python_file_path: Path to a ``.py`` file defining ``call_agent()``.
            architecture: Architecture profile ID (e.g. ``hierarchical``).

        Raises:
            ValueError: If the architecture ID is unknown.
        """
        super().__init__(python_file_path)
        self.architecture_profile: ArchitectureProfile = get_architecture(architecture)
        self._supports_agent_id = False

    def load(self) -> None:
        """
        Load the entrypoint and detect multi-agent ``agent_id`` support.

        After loading, logs whether the entrypoint supports per-agent routing
        and warns when a multi-agent architecture is configured but the
        entrypoint only exposes a single-agent signature.

        Raises:
            FileNotFoundError: If the entrypoint path does not exist.
            ImportError: If the module cannot be executed.
            AttributeError: If ``call_agent`` is not defined.
        """
        super().load()
        if self._call_agent_fn is None:
            return

        signature = inspect.signature(self._call_agent_fn)
        self._supports_agent_id = "agent_id" in signature.parameters

        if self.architecture_profile.is_multi_agent() and not self._supports_agent_id:
            logger.warning(
                "Multi-agent architecture configured but entrypoint lacks agent_id; "
                "experiments will use single-agent fallback",
                extra={
                    "architecture": self.architecture_profile.id.value,
                    "path": str(self._python_file_path),
                },
            )

        logger.info(
            "Multi-agent entrypoint loaded",
            extra={
                "path": str(self._python_file_path),
                "supports_agent_id": self._supports_agent_id,
                "architecture": self.architecture_profile.id.value,
                "agents": self.architecture_profile.agent_ids,
            },
        )

    @property
    def supports_multi_agent(self) -> bool:
        """
        Whether the loaded entrypoint accepts an ``agent_id`` parameter.

        Returns:
            True when ``call_agent`` declares ``agent_id`` in its signature.
        """
        return self._supports_agent_id

    def _validate_agent_id(self, agent_id: str) -> None:
        """
        Warn when routing to an agent ID not declared in the architecture profile.

        Args:
            agent_id: Target agent identifier for the upcoming call.
        """
        if (
            self.architecture_profile.is_multi_agent()
            and agent_id not in self.architecture_profile.agent_ids
        ):
            logger.warning(
                "Routing to agent_id not in architecture profile",
                extra={
                    "agent_id": agent_id,
                    "known_agents": self.architecture_profile.agent_ids,
                    "architecture": self.architecture_profile.id.value,
                },
            )

    async def call_agent(
        self,
        messages: list[dict[str, Any]],
        context_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Invoke ``call_agent`` for a specific agent when supported.

        When the entrypoint supports ``agent_id``, the call is routed to
        ``agent_id`` or the profile's ``entry_agent_id`` by default. Injector
        ``attach_kwargs`` are forwarded when the entrypoint accepts ``**kwargs``.

        Args:
            messages: OpenAI-style message list with ``role`` and ``content``.
            context_id: Optional session identifier for stateful agents.
            agent_id: Target agent; defaults to ``entry_agent_id`` from profile.
            **kwargs: Per-turn side-data (e.g. injector ``attach_kwargs``).

        Returns:
            Agent response string (empty string if the function returns None).

        Raises:
            RuntimeError: If ``load()`` has not been called.
            Exception: Re-raises exceptions from the user's ``call_agent``.
        """
        target_agent = agent_id or self.architecture_profile.entry_agent_id
        self._validate_agent_id(target_agent)

        if self._supports_agent_id:
            return await self._call_with_agent_id(
                messages,
                context_id=context_id,
                agent_id=target_agent,
                **kwargs,
            )

        if agent_id and agent_id not in (
            self.architecture_profile.entry_agent_id,
            "default",
        ):
            logger.debug(
                "Entrypoint lacks agent_id; using single-agent call",
                extra={"requested_agent_id": agent_id},
            )
        return await super().call_agent(messages, context_id=context_id, **kwargs)

    async def _call_with_agent_id(
        self,
        messages: list[dict[str, Any]],
        context_id: Optional[str],
        agent_id: str,
        **kwargs: Any,
    ) -> str:
        """
        Invoke ``call_agent`` with explicit ``agent_id`` routing.

        Args:
            messages: OpenAI-style message list.
            context_id: Optional session identifier.
            agent_id: Target agent to route the call to.
            **kwargs: Forwarded when the entrypoint accepts ``**kwargs``.

        Returns:
            Agent response string.

        Raises:
            RuntimeError: If the entrypoint is not loaded.
            Exception: Re-raises exceptions from the user's ``call_agent``.
        """
        if self._call_agent_fn is None:
            raise RuntimeError("Python entrypoint not loaded. Call load() first.")

        fn = self._call_agent_fn
        call_kwargs: dict[str, Any] = {"agent_id": agent_id}
        signature = inspect.signature(fn)
        params = signature.parameters

        if "context_id" in params:
            call_kwargs["context_id"] = context_id
        if kwargs and any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        ):
            call_kwargs.update(kwargs)
        elif kwargs:
            logger.debug(
                "Dropping kwargs; call_agent does not accept **kwargs",
                extra={"agent_id": agent_id, "keys": list(kwargs.keys())},
            )

        try:
            if asyncio.iscoroutinefunction(fn):
                result = await fn(messages, **call_kwargs)
            else:
                result = await asyncio.to_thread(fn, messages, **call_kwargs)
        except Exception as exc:
            logger.error(
                "Multi-agent call_agent failed",
                extra={
                    "agent_id": agent_id,
                    "context_id": context_id,
                    "path": str(self._python_file_path),
                    "error": str(exc),
                },
            )
            raise

        return str(result) if result is not None else ""
