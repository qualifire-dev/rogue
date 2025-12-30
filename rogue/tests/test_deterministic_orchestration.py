"""
Tests for deterministic red team orchestration.

Tests the new deterministic orchestration mode to ensure reproducibility and stability.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from rogue.evaluator_agent.attack_message_generator import AttackMessageGenerator
from rogue.evaluator_agent.attack_templates import ATTACK_TEMPLATES
from rogue.evaluator_agent.red_team_orchestrator import RedTeamOrchestrator


@pytest.fixture
def orchestrator():
    """Create a deterministic orchestrator with fixed seed."""
    return RedTeamOrchestrator(
        random_seed=42,
        min_turns_per_session=3,
        max_turns_per_session=5,
    )


@pytest.fixture
def message_generator():
    """Create a message generator with templates."""
    return AttackMessageGenerator(
        templates=ATTACK_TEMPLATES,
        adaptive_follow_ups=False,
        random_seed=42,
    )


@pytest.fixture
def mock_category():
    """Create a mock OWASP category."""
    mock_attack = MagicMock()
    mock_attack.get_name.return_value = "Prompt Injection"
    mock_attack.get_strategy_id.return_value = "prompt_injection"
    mock_attack.enhance.side_effect = lambda x: x
    mock_attack.weight = 1

    mock_cat = MagicMock()
    mock_cat.id = "LLM_01"
    mock_cat.name = "Prompt Injection"
    mock_cat.attacks = [mock_attack]
    mock_cat.vulnerabilities = []

    return mock_cat


@pytest.fixture
def mock_framework(mock_category):
    """Create a mock OWASP framework."""
    mock_fw = MagicMock()
    mock_fw.get_categories.return_value = [mock_category]
    return mock_fw


def test_orchestrator_deterministic_seed():
    """Test that orchestrator with seed produces deterministic behavior."""
    orch1 = RedTeamOrchestrator(random_seed=42)
    orch2 = RedTeamOrchestrator(random_seed=42)

    # Both should select same attack for same session number
    mock_attacks = [MagicMock() for _ in range(5)]
    for attack in mock_attacks:
        attack.weight = 1

    selected1 = orch1._select_attack(mock_attacks, 0)
    selected2 = orch2._select_attack(mock_attacks, 0)

    assert selected1 == selected2


def test_orchestrator_different_seeds():
    """Test that different seeds produce different selection."""
    orch1 = RedTeamOrchestrator(random_seed=42)
    orch2 = RedTeamOrchestrator(random_seed=123)

    mock_attacks = [MagicMock() for _ in range(5)]
    for attack in mock_attacks:
        attack.weight = 1

    # With enough diversity, different seeds should select different attacks
    # (probabilistically - may fail occasionally)
    selections1 = [orch1._select_attack(mock_attacks, i) for i in range(10)]
    selections2 = [orch2._select_attack(mock_attacks, i) for i in range(10)]

    # At least one selection should differ
    assert any(s1 != s2 for s1, s2 in zip(selections1, selections2))


def test_orchestrator_turn_counting():
    """Test that orchestrator correctly counts turns."""
    orch = RedTeamOrchestrator(
        random_seed=42,
        min_turns_per_session=3,
        max_turns_per_session=5,
    )

    turns = [orch._determine_num_turns() for _ in range(10)]

    # All turns should be within range
    assert all(3 <= t <= 5 for t in turns)

    # With deterministic seed, turns should follow pattern
    _ = [orch._determine_num_turns() for _ in range(10)]
    # Note: After sessions are created, the pattern changes
    # Just verify they're in range


def test_orchestrator_progress_tracking(orchestrator):
    """Test progress tracking."""
    categories = ["LLM_01", "LLM_02"]

    # Simulate some completed sessions
    orchestrator._category_test_counts["LLM_01"] = 3
    orchestrator._category_test_counts["LLM_02"] = 1
    orchestrator._total_sessions = 4
    orchestrator._completed_sessions = 4

    progress = orchestrator._get_progress_report(categories, min_tests_per_attack=3)

    assert progress["total_categories"] == 2
    assert progress["categories_completed"] == 1  # Only LLM_01 reached min
    assert progress["categories_in_progress"] == 1  # LLM_02 in progress
    assert progress["total_sessions"] == 4


@pytest.mark.asyncio
async def test_execute_attack_session(orchestrator, message_generator, mock_category):
    """Test executing a single attack session."""
    mock_sender = AsyncMock(return_value={"response": "Test response"})
    mock_evaluator = AsyncMock()
    mock_registrar = MagicMock()

    attack = mock_category.attacks[0]

    await orchestrator.execute_attack_session(
        category=mock_category,
        attack=attack,
        session_num=0,
        message_generator=message_generator,
        message_sender=mock_sender,
        response_evaluator=mock_evaluator,
        context_registrar=mock_registrar,
    )

    # Should have sent multiple messages (3-5 turns)
    assert mock_sender.call_count >= 3
    assert mock_sender.call_count <= 5

    # Should have registered the context
    assert mock_registrar.call_count == 1

    # Should have evaluated each response
    assert mock_evaluator.call_count >= 3


def test_message_generator_template_selection():
    """Test template-based message generation."""
    gen = AttackMessageGenerator(
        templates=ATTACK_TEMPLATES,
        adaptive_follow_ups=False,
        random_seed=42,
    )

    mock_category = MagicMock()
    mock_category.id = "LLM_01"
    mock_category.name = "Prompt Injection"

    mock_attack = MagicMock()
    mock_attack.get_name.return_value = "Prompt Injection"
    mock_attack.enhance.side_effect = lambda x: x

    # Generate message
    message = gen._generate_from_template(
        category=mock_category,
        attack=mock_attack,
        context_id="test123",
    )

    # Should return a valid template message
    assert isinstance(message, str)
    assert len(message) > 0


def test_message_generator_deterministic():
    """Test that message generator with seed is deterministic."""
    gen1 = AttackMessageGenerator(
        templates=ATTACK_TEMPLATES,
        adaptive_follow_ups=False,
        random_seed=42,
    )

    gen2 = AttackMessageGenerator(
        templates=ATTACK_TEMPLATES,
        adaptive_follow_ups=False,
        random_seed=42,
    )

    mock_category = MagicMock()
    mock_category.id = "LLM_01"
    mock_category.name = "Prompt Injection"

    mock_attack = MagicMock()
    mock_attack.get_name.return_value = "Prompt Injection"
    mock_attack.enhance.side_effect = lambda x: x

    # Same context ID should produce same message
    msg1 = gen1._generate_from_template(mock_category, mock_attack, "test123")
    msg2 = gen2._generate_from_template(mock_category, mock_attack, "test123")

    assert msg1 == msg2


def test_message_generator_escalation():
    """Test escalation message generation."""
    gen = AttackMessageGenerator(
        templates=ATTACK_TEMPLATES,
        adaptive_follow_ups=False,
        random_seed=42,
    )

    mock_category = MagicMock()
    mock_category.id = "LLM_01"
    mock_category.name = "Prompt Injection"

    mock_attack = MagicMock()
    mock_attack.get_name.return_value = "Prompt Injection"

    # Generate escalation message
    message = gen._generate_escalation_from_template(
        category=mock_category,
        attack=mock_attack,
        turn_num=2,
        context_id="test123",
    )

    assert isinstance(message, str)
    assert len(message) > 0


@pytest.mark.asyncio
async def test_full_testing_suite(orchestrator, message_generator, mock_framework):
    """Test running a full testing suite."""
    mock_sender = AsyncMock(return_value={"response": "Test response"})
    mock_evaluator = AsyncMock()
    mock_registrar = MagicMock()

    results = await orchestrator.run_testing_suite(
        categories=["LLM_01"],
        owasp_framework=mock_framework,
        min_tests_per_attack=2,
        message_generator=message_generator,
        message_sender=mock_sender,
        response_evaluator=mock_evaluator,
        context_registrar=mock_registrar,
    )

    # Should have completed testing
    assert results["total_categories"] == 1
    assert results["categories_completed"] == 1
    assert results["all_complete"] is True
    assert results["total_sessions"] == 2

    # Should have sent messages for each session
    assert mock_sender.call_count >= 6  # 2 sessions * 3 min turns


def test_attack_templates_exist():
    """Test that attack templates are properly defined."""
    # Check major categories exist
    assert "LLM_01" in ATTACK_TEMPLATES
    assert "LLM_02" in ATTACK_TEMPLATES
    assert "generic" in ATTACK_TEMPLATES

    # Check templates have content
    llm01_templates = ATTACK_TEMPLATES["LLM_01"]
    assert "prompt_injection" in llm01_templates
    assert len(llm01_templates["prompt_injection"]) > 0

    # Check escalation templates exist
    has_escalation = (
        "escalation" in llm01_templates
        or "prompt_injection_escalation" in llm01_templates
    )
    assert has_escalation


def test_template_fallbacks():
    """Test that template system has proper fallbacks."""
    from rogue.evaluator_agent.attack_templates import get_template

    # Test specific template
    templates = get_template("LLM_01", "prompt_injection")
    assert len(templates) > 0

    # Test fallback to generic
    templates = get_template("NONEXISTENT", "nonexistent")
    assert len(templates) > 0  # Should fallback to generic

    # Test without fallback
    templates = get_template("NONEXISTENT", "nonexistent", fallback=False)
    assert len(templates) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
