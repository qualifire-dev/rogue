"""Tests for resilience scenario generation."""

import pytest

from rogue.server.api.resilience import (
    ResilienceScenarioGenerateRequest,
    generate_resilience_scenarios,
)
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


@pytest.mark.asyncio
async def test_generate_route_offloads_blocking_generate(mocker) -> None:
    templates = ResilienceScenarioService().generate("", count=1)
    mock_to_thread = mocker.patch(
        "rogue.server.api.resilience.asyncio.to_thread",
        new=mocker.AsyncMock(return_value=templates),
    )
    request = ResilienceScenarioGenerateRequest(
        business_context="E-commerce refund bot",
        model="openai/gpt-4o-mini",
    )

    response = await generate_resilience_scenarios(request)

    mock_to_thread.assert_awaited_once()
    assert response.scenarios == templates
