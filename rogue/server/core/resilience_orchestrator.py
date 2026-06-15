"""
Server-side wrapper for the resilience orchestrator.

Mirrors ``server/core/red_team_orchestrator.py`` — connects job requests to
the engine orchestrator in ``rogue/resilience/orchestrator.py``.
"""

from typing import Any, AsyncGenerator, Optional, Tuple

from rogue_sdk.types import AuthType, Protocol, ResilienceConfig, Transport

from ...common.logging import get_logger
from ...resilience.models import ArchitectureId
from ...resilience.orchestrator import ResilienceOrchestrator

logger = get_logger(__name__)


class ServerResilienceOrchestrator:
    """
    Coordinates resilience experiments against a target agent from the server.

    Translates ``ResilienceRequest`` fields into a ``ResilienceOrchestrator``
    engine instance and streams progress updates back to ``ResilienceService``.

    Phase 1 supports the PYTHON protocol only. Additional protocol adapters
    will be added in Phase 2 via ``evaluator_agent/resilience/``.
    """

    def __init__(
        self,
        protocol: Protocol,
        transport: Optional[Transport],
        evaluated_agent_url: str,
        evaluated_agent_auth_type: AuthType,
        evaluated_agent_auth_credentials: Optional[str],
        resilience_config: ResilienceConfig,
        judge_llm: str,
        judge_llm_api_key: Optional[str] = None,
        judge_llm_api_base: Optional[str] = None,
        judge_llm_api_version: Optional[str] = None,
        business_context: str = "",
        python_entrypoint_file: Optional[str] = None,
    ) -> None:
        """
        Initialize the server orchestrator wrapper.

        Args:
            protocol: Target agent protocol (Phase 1: ``PYTHON`` only).
            transport: Transport for network protocols (unused in Phase 1).
            evaluated_agent_url: Agent URL for network protocols.
            evaluated_agent_auth_type: Authentication mode for the target.
            evaluated_agent_auth_credentials: Credentials for the target agent.
            resilience_config: Injector list, tasks, and metric settings.
            judge_llm: Judge model name (required by API even for heuristics).
            judge_llm_api_key: API key for the judge LLM.
            judge_llm_api_base: Optional custom judge API base.
            judge_llm_api_version: Optional judge API version.
            business_context: Domain description for metrics and injectors.
            python_entrypoint_file: Path to ``call_agent`` entrypoint (PYTHON).
        """
        self.protocol = protocol
        self.transport = transport
        self.evaluated_agent_url = evaluated_agent_url
        self.evaluated_agent_auth_type = evaluated_agent_auth_type
        self.evaluated_agent_auth_credentials = evaluated_agent_auth_credentials
        self.resilience_config = resilience_config
        self.judge_llm = judge_llm
        self.judge_llm_api_key = judge_llm_api_key
        self.judge_llm_api_base = judge_llm_api_base
        self.judge_llm_api_version = judge_llm_api_version
        self.business_context = business_context
        self.python_entrypoint_file = python_entrypoint_file
        self.logger = get_logger(__name__)

    def _build_engine(self) -> ResilienceOrchestrator:
        """
        Construct the engine orchestrator from job configuration.

        Returns:
            Configured ``ResilienceOrchestrator`` ready to run experiments.

        Raises:
            NotImplementedError: If protocol is not PYTHON (Phase 1 limit).
            ValueError: If PYTHON protocol is missing an entrypoint file.
        """
        if self.protocol != Protocol.PYTHON:
            raise NotImplementedError(
                f"Resilience Phase 1 supports PYTHON protocol only; got {self.protocol}",
            )
        if not self.python_entrypoint_file:
            raise ValueError("python_entrypoint_file is required for PYTHON protocol")

        try:
            architecture = ArchitectureId(self.resilience_config.architecture)
        except ValueError:
            self.logger.warning(
                "Unknown architecture ID; falling back to single_agent",
                extra={"architecture": self.resilience_config.architecture},
            )
            architecture = ArchitectureId.SINGLE_AGENT

        if not self.resilience_config.injectors:
            raise ValueError("resilience_config.injectors must not be empty")

        for plugin_path in self.resilience_config.custom_injector_plugins:
            try:
                from rogue.injectors.plugins import load_injector_plugin

                load_injector_plugin(plugin_path)
            except Exception as exc:
                self.logger.warning(
                    "Failed to load custom injector plugin",
                    extra={"path": plugin_path, "error": str(exc)},
                )

        return ResilienceOrchestrator(
            injectors=self.resilience_config.injectors,
            python_entrypoint_file=self.python_entrypoint_file,
            business_context=self.business_context,
            baseline_task=self.resilience_config.baseline_task,
            recovery_task=self.resilience_config.recovery_task,
            architecture=architecture,
            target_agent_id=self.resilience_config.target_agent_id,
            experiments_per_injector=self.resilience_config.experiments_per_injector,
            judge_llm=self.judge_llm,
            judge_llm_auth=self.judge_llm_api_key,
            judge_llm_api_base=self.judge_llm_api_base,
            judge_llm_api_version=self.judge_llm_api_version,
            use_heuristics=self.resilience_config.use_heuristics,
            injector_intensity=self.resilience_config.injector_intensity,
            enable_checkpoint_recovery=self.resilience_config.enable_checkpoint_recovery,
            checkpoint_thread_id=self.resilience_config.checkpoint_thread_id,
            concurrent_target_agent_ids=self.resilience_config.concurrent_target_agent_ids,
        )

    async def run_experiments(self) -> AsyncGenerator[Tuple[str, Any], None]:
        """
        Run resilience experiments and yield progress updates.

        Yields:
            Tuple[str, Any]: ``(update_type, data)`` where ``update_type`` is
            one of ``status``, ``trace``, ``experiment``, or ``results``.

        Raises:
            NotImplementedError: If an unsupported protocol is configured.
            ValueError: If required PYTHON entrypoint configuration is missing.
            FileNotFoundError: If the entrypoint file cannot be loaded.
        """
        engine = self._build_engine()
        self.logger.info(
            "Starting server resilience experiments",
            extra={
                "injectors": self.resilience_config.injectors,
                "architecture": self.resilience_config.architecture,
                "entrypoint": self.python_entrypoint_file,
            },
        )
        try:
            async for update_type, data in engine.run_experiments_streaming():
                yield update_type, data
        except Exception as exc:
            self.logger.exception(
                "Resilience experiment stream failed",
                extra={"error": str(exc)},
            )
            raise
