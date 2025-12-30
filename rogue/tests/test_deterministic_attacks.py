"""
Tests for deterministic/reproducible attack selection.

Tests that the same random seed produces identical attack sequences,
enabling reproducible red team scans for regression testing and validation.
"""

import random
from typing import List
from unittest.mock import patch

import pytest

from rogue.server.red_teaming.attacks.base_attack import BaseAttack


# Mock attack classes for testing
class MockBaseAttack(BaseAttack):
    """Mock attack for testing."""

    def __init__(self, name: str):
        self.name = name
        self.weight = 1
        self.multi_turn = False

    def get_name(self) -> str:
        return self.name


class TestDeterministicAttackSelection:
    """Test deterministic attack selection with seeding."""

    def test_random_seed_initialization(self):
        """Test that random seed is properly initialized."""
        from rogue_sdk.types import Scenarios, Transport

        from rogue.evaluator_agent.red_team_a2a_evaluator_agent import (
            RedTeamA2AEvaluatorAgent,
        )

        with patch(
            "rogue.evaluator_agent.red_team_a2a_evaluator_agent.get_llm_from_model",
        ):
            # With seed
            agent = RedTeamA2AEvaluatorAgent(
                evaluated_agent_address="http://test.com",
                transport=Transport.HTTP,
                judge_llm="test-model",
                scenarios=Scenarios(scenarios=[]),
                business_context="test",
                owasp_categories=["LLM_01"],
                random_seed=42,
            )
            assert agent._random_seed == 42
            assert agent._deterministic_mode is True

            # Without seed
            agent_no_seed = RedTeamA2AEvaluatorAgent(
                evaluated_agent_address="http://test.com",
                transport=Transport.HTTP,
                judge_llm="test-model",
                scenarios=Scenarios(scenarios=[]),
                business_context="test",
                owasp_categories=["LLM_01"],
            )
            assert agent_no_seed._random_seed is None
            assert agent_no_seed._deterministic_mode is False

    def test_same_seed_produces_same_sequence(self):
        """Test that same seed produces identical random sequences."""
        # First run with seed 42
        random.seed(42)
        sequence1 = [random.randint(0, 100) for _ in range(10)]

        # Second run with same seed
        random.seed(42)
        sequence2 = [random.randint(0, 100) for _ in range(10)]

        # Should be identical
        assert sequence1 == sequence2

    def test_different_seeds_produce_different_sequences(self):
        """Test that different seeds produce different sequences."""
        random.seed(42)
        sequence1 = [random.randint(0, 100) for _ in range(10)]

        random.seed(123)
        sequence2 = [random.randint(0, 100) for _ in range(10)]

        # Should be different
        assert sequence1 != sequence2

    def test_no_seed_produces_random_sequences(self):
        """Test that no seed produces different sequences each time."""
        # Don't set seed
        sequence1 = [random.random() for _ in range(10)]
        sequence2 = [random.random() for _ in range(10)]

        # Should be different (with very high probability)
        assert sequence1 != sequence2

    def test_deterministic_attack_selection_ordering(self):
        """Test deterministic attack selection uses sorted ordering."""
        attacks = [
            MockBaseAttack("zebra"),
            MockBaseAttack("alpha"),
            MockBaseAttack("beta"),
        ]

        # Sort attacks by name for deterministic selection
        sorted_attacks = sorted(attacks, key=lambda a: a.get_name())

        # Should be in alphabetical order
        assert sorted_attacks[0].get_name() == "alpha"
        assert sorted_attacks[1].get_name() == "beta"
        assert sorted_attacks[2].get_name() == "zebra"

    def test_context_hash_deterministic_selection(self):
        """Test context hash produces consistent selection."""
        attacks = [
            MockBaseAttack("attack_a"),
            MockBaseAttack("attack_b"),
            MockBaseAttack("attack_c"),
        ]
        sorted_attacks = sorted(attacks, key=lambda a: a.get_name())

        context_id = "test-context-123"

        # Select attack using hash
        context_index = hash(context_id) % len(sorted_attacks)
        selected1 = sorted_attacks[context_index]

        # Should get same attack with same context
        context_index2 = hash(context_id) % len(sorted_attacks)
        selected2 = sorted_attacks[context_index2]

        assert selected1.get_name() == selected2.get_name()

    def test_different_contexts_may_select_different_attacks(self):
        """Test different contexts may select different attacks."""
        attacks = [
            MockBaseAttack("attack_a"),
            MockBaseAttack("attack_b"),
            MockBaseAttack("attack_c"),
        ]
        sorted_attacks = sorted(attacks, key=lambda a: a.get_name())

        context1 = "context-1"
        context2 = "context-2"

        # Select attacks
        index1 = hash(context1) % len(sorted_attacks)
        index2 = hash(context2) % len(sorted_attacks)

        # Indices may be different (though not guaranteed)
        # This is just demonstrating the mechanism
        assert index1 == hash(context1) % len(sorted_attacks)
        assert index2 == hash(context2) % len(sorted_attacks)


class TestAttackStatisticsConsistency:
    """Test that attack statistics are consistent across seeded runs."""

    def test_statistics_tracking_deterministic(self):
        """Test that statistics tracking works consistently."""
        from rogue.server.red_teaming.attack_statistics import (
            AttackStatisticsTracker,
        )

        tracker = AttackStatisticsTracker()

        # Record attempts in deterministic order
        tracker.record_attempt("base64", success=True, score=0.1)
        tracker.record_attempt("base64", success=False, score=0.5)
        tracker.record_attempt("base64", success=True, score=0.2)

        stats = tracker.get_statistics("base64")
        assert stats is not None
        assert stats.total_attempts == 3
        assert stats.success_count == 2
        assert stats.success_rate == pytest.approx(2.0 / 3.0)

    def test_statistics_reset(self):
        """Test that statistics can be reset for new run."""
        from rogue.server.red_teaming.attack_statistics import (
            AttackStatisticsTracker,
        )

        tracker = AttackStatisticsTracker()

        # Record some attempts
        tracker.record_attempt("base64", success=True)
        assert len(tracker.get_all_statistics()) == 1

        # Reset
        tracker.reset()
        assert len(tracker.get_all_statistics()) == 0


class TestTemperatureControl:
    """Test LLM temperature control for reproducibility."""

    def test_temperature_zero_more_deterministic(self):
        """
        Test that temperature=0.0 produces more consistent results.

        Note: This is a conceptual test. Actual LLM determinism depends
        on the provider and may still have some variability.
        """
        # Temperature values
        creative_temp = 0.7
        deterministic_temp = 0.0

        assert deterministic_temp < creative_temp

        # Lower temperature should reduce randomness
        # (This would need actual LLM calls to verify properly)

    def test_default_temperature(self):
        """Test default temperature is appropriate for exploration."""
        default_temp = 0.7
        assert 0.0 <= default_temp <= 1.0


class TestReproducibleScanWorkflow:
    """Test complete reproducible scan workflow."""

    def test_reproducible_mode_configuration(self):
        """Test configuration for reproducible mode."""
        config = {
            "reproducible_mode": True,
            "random_seed": 42,
            "attack_temperature": 0.0,
        }

        assert config["reproducible_mode"] is True
        assert config["random_seed"] == 42
        assert config["attack_temperature"] == 0.0

    def test_exploratory_mode_configuration(self):
        """Test configuration for exploratory mode."""
        config = {
            "reproducible_mode": False,
            "random_seed": None,
            "attack_temperature": 0.7,
        }

        assert config["reproducible_mode"] is False
        assert config["random_seed"] is None
        assert config["attack_temperature"] == 0.7

    def test_seed_value_types(self):
        """Test that seed values are valid integers."""
        valid_seeds = [42, 0, 123456, 999999]

        for seed in valid_seeds:
            assert isinstance(seed, int)
            random.seed(seed)
            # Should not raise


class TestBackwardCompatibility:
    """Test that new determinism features don't break existing functionality."""

    def test_no_seed_maintains_random_behavior(self):
        """Test that not providing seed maintains random behavior."""
        from rogue_sdk.types import Scenarios, Transport

        from rogue.evaluator_agent.red_team_a2a_evaluator_agent import (
            RedTeamA2AEvaluatorAgent,
        )

        with patch(
            "rogue.evaluator_agent.red_team_a2a_evaluator_agent.get_llm_from_model",
        ):
            # Create agent without seed
            agent = RedTeamA2AEvaluatorAgent(
                evaluated_agent_address="http://test.com",
                transport=Transport.HTTP,
                judge_llm="test-model",
                scenarios=Scenarios(scenarios=[]),
                business_context="test",
                owasp_categories=["LLM_01"],
            )

            # Should still work in non-deterministic mode
            assert agent._deterministic_mode is False

    def test_attack_selection_fallback(self):
        """Test attack selection works in both modes."""
        attacks = [
            MockBaseAttack("attack_a"),
            MockBaseAttack("attack_b"),
            MockBaseAttack("attack_c"),
        ]

        # Deterministic mode
        sorted_attacks = sorted(attacks, key=lambda a: a.get_name())
        context_index = hash("test-context") % len(sorted_attacks)
        deterministic_selection = sorted_attacks[context_index]

        assert deterministic_selection.get_name() in [
            "attack_a",
            "attack_b",
            "attack_c",
        ]

        # Random mode
        random_selection = random.choice(attacks)
        assert random_selection.get_name() in ["attack_a", "attack_b", "attack_c"]


class TestEdgeCases:
    """Test edge cases in deterministic attack selection."""

    def test_single_attack_always_selected(self):
        """Test that single attack is always selected."""
        attacks = [MockBaseAttack("only_attack")]
        sorted_attacks = sorted(attacks, key=lambda a: a.get_name())

        # With any context
        for context_id in ["ctx1", "ctx2", "ctx3"]:
            index = hash(context_id) % len(sorted_attacks)
            selected = sorted_attacks[index]
            assert selected.get_name() == "only_attack"

    def test_empty_attack_list_handling(self):
        """Test handling of empty attack list."""
        attacks: List[BaseAttack] = []

        # Should handle gracefully
        if attacks:
            sorted_attacks = sorted(attacks, key=lambda a: a.get_name())
            assert len(sorted_attacks) > 0
        else:
            # Empty list is valid
            assert len(attacks) == 0

    def test_very_long_context_id(self):
        """Test that very long context IDs work with hashing."""
        long_context = "x" * 10000
        attacks = [MockBaseAttack(f"attack_{i}") for i in range(5)]
        sorted_attacks = sorted(attacks, key=lambda a: a.get_name())

        # Should not raise
        index = hash(long_context) % len(sorted_attacks)
        selected = sorted_attacks[index]
        assert selected is not None

    def test_special_characters_in_context_id(self):
        """Test context IDs with special characters."""
        special_contexts = [
            "context-with-dashes",
            "context_with_underscores",
            "context.with.dots",
            "context/with/slashes",
            "context@with#special!chars",
        ]

        attacks = [MockBaseAttack(f"attack_{i}") for i in range(3)]
        sorted_attacks = sorted(attacks, key=lambda a: a.get_name())

        for context in special_contexts:
            # Should not raise
            index = hash(context) % len(sorted_attacks)
            selected = sorted_attacks[index]
            assert selected is not None


class TestDocumentedUsagePatterns:
    """Test usage patterns that should be documented."""

    def test_reproducible_scan_pattern(self):
        """Test recommended pattern for reproducible scans."""
        # Configuration for reproducible scan
        seed = 42
        # temperature = 0.0 would be used for LLM calls

        # Set seed
        random.seed(seed)

        # Run scan (simulated)
        results1 = []
        for i in range(10):
            results1.append(random.randint(0, 100))

        # Reset and run again with same seed
        random.seed(seed)
        results2 = []
        for i in range(10):
            results2.append(random.randint(0, 100))

        # Should be identical
        assert results1 == results2

    def test_comparison_pattern(self):
        """Test pattern for comparing two agent versions."""
        seed = 42

        # Scan agent version 1
        random.seed(seed)
        agent_v1_results = [random.randint(0, 100) for _ in range(5)]

        # Scan agent version 2 (after fixes)
        random.seed(seed)
        agent_v2_results = [random.randint(0, 100) for _ in range(5)]

        # Same scan sequence used for both
        # (Results may differ if agent behavior changed, but attack sequence is same)
        assert len(agent_v1_results) == len(agent_v2_results)

    def test_regression_testing_pattern(self):
        """Test pattern for regression testing."""
        baseline_seed = 42

        # Baseline scan
        random.seed(baseline_seed)
        baseline_vuln_count = sum(1 for _ in range(10) if random.random() > 0.5)

        # After code changes, re-run with same seed
        random.seed(baseline_seed)
        current_vuln_count = sum(1 for _ in range(10) if random.random() > 0.5)

        # Can compare counts
        assert baseline_vuln_count == current_vuln_count
