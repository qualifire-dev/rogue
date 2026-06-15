"""
Python protocol resilience evaluator agent.
"""

from rogue.resilience.models import ResilienceResults

from .base_resilience_evaluator import BaseResilienceEvaluatorAgent


class PythonResilienceEvaluatorAgent(BaseResilienceEvaluatorAgent):
    """
    Resilience evaluator for Python ``call_agent`` entrypoints.

    Supports single-agent and multi-agent entrypoints (with ``agent_id``).
    """

    async def run_experiments(self) -> ResilienceResults:
        """
        Run resilience experiments via the engine orchestrator.

        Returns:
            Aggregated experiment results and metrics.
        """
        orchestrator = self.build_orchestrator()
        return await orchestrator.run_experiments()
