"""
Base resilience evaluator agent for connecting to target multi-agent systems.

Parallel to ``BaseEvaluatorAgent`` but focused on chaos experiment execution
rather than policy scenario judging.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from rogue.resilience.models import ArchitectureId, ResilienceResults
from rogue.resilience.orchestrator import ResilienceOrchestrator


class BaseResilienceEvaluatorAgent(ABC):
    """
    Abstract adapter that runs resilience experiments against a target system.

    Subclasses implement protocol-specific connectivity; the orchestrator
    engine performs inject → observe → measure → recover.
    """

    def __init__(
        self,
        python_entrypoint_file: str,
        injectors: list[str],
        architecture: ArchitectureId = ArchitectureId.SINGLE_AGENT,
        business_context: str = "",
        target_agent_id: str = "default",
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
        use_heuristics: bool = True,
        enable_checkpoint_recovery: bool = False,
        checkpoint_adapter: Optional[Any] = None,
    ) -> None:
        self.python_entrypoint_file = python_entrypoint_file
        self.injectors = injectors
        self.architecture = architecture
        self.business_context = business_context
        self.target_agent_id = target_agent_id
        self.judge_llm = judge_llm
        self.judge_llm_auth = judge_llm_auth
        self.use_heuristics = use_heuristics
        self.enable_checkpoint_recovery = enable_checkpoint_recovery
        self.checkpoint_adapter = checkpoint_adapter

    def build_orchestrator(self) -> ResilienceOrchestrator:
        """
        Construct the engine orchestrator from this adapter's configuration.

        Returns:
            Configured ``ResilienceOrchestrator`` ready to run experiments.
        """
        return ResilienceOrchestrator(
            injectors=self.injectors,
            python_entrypoint_file=self.python_entrypoint_file,
            business_context=self.business_context,
            architecture=self.architecture,
            target_agent_id=self.target_agent_id,
            judge_llm=self.judge_llm,
            judge_llm_auth=self.judge_llm_auth,
            use_heuristics=self.use_heuristics,
            enable_checkpoint_recovery=self.enable_checkpoint_recovery,
            checkpoint_adapter=self.checkpoint_adapter,
        )

    @abstractmethod
    async def run_experiments(self) -> ResilienceResults:
        """Run resilience experiments against the configured target."""
