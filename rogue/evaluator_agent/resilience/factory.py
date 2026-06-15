"""
Factory for resilience evaluator agents.
"""

from typing import Any, Optional

from rogue_sdk.types import Protocol

from rogue.resilience.models import ArchitectureId

from .base_resilience_evaluator import BaseResilienceEvaluatorAgent
from .python_resilience_evaluator import PythonResilienceEvaluatorAgent


def create_resilience_evaluator_agent(
    protocol: Protocol,
    python_entrypoint_file: str,
    injectors: list[str],
    architecture: ArchitectureId | str = ArchitectureId.SINGLE_AGENT,
    business_context: str = "",
    target_agent_id: str = "default",
    judge_llm: Optional[str] = None,
    judge_llm_auth: Optional[str] = None,
    use_heuristics: bool = True,
    enable_checkpoint_recovery: bool = False,
    checkpoint_adapter: Optional[Any] = None,
) -> BaseResilienceEvaluatorAgent:
    """
    Create a resilience evaluator agent for the given protocol.

    Phase 2 supports ``Protocol.PYTHON`` only; other protocols raise
    ``NotImplementedError``.

    Args:
        protocol: Target agent protocol.
        python_entrypoint_file: Path to ``call_agent`` entrypoint.
        injectors: Injector IDs to run.
        architecture: Multi-agent architecture profile.
        business_context: Domain context for metrics.
        target_agent_id: Agent to inject faults into.
        judge_llm: Optional judge model name.
        judge_llm_auth: Optional judge API key.
        use_heuristics: Use heuristic metrics when True.
        enable_checkpoint_recovery: Enable checkpoint restore when True.
        checkpoint_adapter: Optional checkpoint adapter instance.

    Returns:
        Configured resilience evaluator agent.

    Raises:
        NotImplementedError: For unsupported protocols.
        ValueError: If PYTHON protocol is missing an entrypoint path.
    """
    if protocol != Protocol.PYTHON:
        raise NotImplementedError(
            f"Resilience Phase 2 supports PYTHON protocol only; got {protocol}",
        )
    if not python_entrypoint_file:
        raise ValueError("python_entrypoint_file is required for PYTHON protocol")

    if isinstance(architecture, str):
        architecture = ArchitectureId(architecture)

    return PythonResilienceEvaluatorAgent(
        python_entrypoint_file=python_entrypoint_file,
        injectors=injectors,
        architecture=architecture,
        business_context=business_context,
        target_agent_id=target_agent_id,
        judge_llm=judge_llm,
        judge_llm_auth=judge_llm_auth,
        use_heuristics=use_heuristics,
        enable_checkpoint_recovery=enable_checkpoint_recovery,
        checkpoint_adapter=checkpoint_adapter,
    )
