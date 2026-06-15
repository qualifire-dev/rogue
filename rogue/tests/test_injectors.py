"""Unit tests for Rogue Resilience fault injectors."""

import pytest

from rogue.injectors.base_injector import InjectionContext, InjectorConfig, InjectorId
from rogue.injectors.registry import INJECTOR_CATALOG, get_injector, list_injectors


@pytest.mark.parametrize(
    "injector_id",
    list(InjectorId),
)
@pytest.mark.asyncio
async def test_injector_produces_probe_messages(injector_id: InjectorId) -> None:
    injector = get_injector(injector_id)
    injector.configure(InjectorConfig(intensity=0.8, max_probe_messages=2))
    context = InjectionContext(
        target_agent_id="worker-1",
        baseline_task="Help the customer",
        business_context="T-shirt store",
    )
    result = await injector.inject("worker-1", context)
    assert result.injector_id == injector_id
    assert result.armed is True
    assert len(result.probe_messages) >= 1
    assert result.probe_messages == injector.get_probe_messages()[:2]
    injector.teardown()
    assert injector.is_armed is False


def test_registry_lists_all_injectors() -> None:
    built_in = [
        entry
        for entry in list_injectors(include_premium=False)
        if not entry.custom and not entry.premium
    ]
    assert len(built_in) == len(InjectorId)
    for injector_id in InjectorId:
        assert injector_id in INJECTOR_CATALOG

    premium = list_injectors(include_premium=True)
    assert len(premium) > len(InjectorId)
    assert "gradual_goal_drift" in INJECTOR_CATALOG


def test_unknown_injector_raises() -> None:
    with pytest.raises(KeyError, match="not_a_real_injector"):
        get_injector("not_a_real_injector")
