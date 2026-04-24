"""Multi-turn policy evaluation driver.

Runs scenarios where the rogue agent dynamically drives a multi-turn conversation
toward a goal (free-form text or stepped plan stored in ``Scenario.scenario``),
stopping on goal-achieved (per-turn LLM check) or ``Scenario.max_turns``.
Pass/fail is still decided by the existing judge LLM against ``expected_outcome``.
"""

from .run_multi_turn import arun_multi_turn_evaluator

__all__ = ["arun_multi_turn_evaluator"]
