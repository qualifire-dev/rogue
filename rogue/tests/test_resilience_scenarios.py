"""Tests for resilience scenario generation."""

from rogue.server.services.resilience_scenario_service import ResilienceScenarioService


def test_fallback_scenarios_without_llm() -> None:
    service = ResilienceScenarioService()
    scenarios = service.generate("", count=3)
    assert len(scenarios) >= 2
    assert scenarios[0].injectors
    assert scenarios[0].architecture


def test_fallback_scenarios_on_empty_context() -> None:
    service = ResilienceScenarioService(model="openai/gpt-4o-mini")
    scenarios = service.generate("   ", count=2)
    assert len(scenarios) >= 2
