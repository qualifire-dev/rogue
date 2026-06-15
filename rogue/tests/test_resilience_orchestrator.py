"""Unit tests for the resilience orchestrator."""

from pathlib import Path

import pytest

from rogue.injectors.base_injector import InjectorId
from rogue.resilience.orchestrator import ResilienceOrchestrator


FIXTURE_AGENT = Path(__file__).parent / "fixtures" / "resilience_test_agent.py"


@pytest.mark.asyncio
async def test_orchestrator_runs_single_injector_experiment() -> None:
    orchestrator = ResilienceOrchestrator(
        injectors=[InjectorId.POLICY_VIOLATION],
        python_entrypoint_file=str(FIXTURE_AGENT),
        business_context="T-shirt store with fixed pricing",
        experiments_per_injector=1,
        use_heuristics=True,
    )
    results = await orchestrator.run_experiments()
    assert results.total_experiments == 1
    assert len(results.experiments) == 1
    experiment = results.experiments[0]
    assert experiment.injector_id == InjectorId.POLICY_VIOLATION
    assert len(experiment.metrics) == 3
    assert experiment.composite_score >= 0.0


@pytest.mark.asyncio
async def test_orchestrator_streaming_yields_results() -> None:
    orchestrator = ResilienceOrchestrator(
        injectors=[InjectorId.ACTION_SPAM],
        python_entrypoint_file=str(FIXTURE_AGENT),
        experiments_per_injector=1,
        use_heuristics=True,
    )
    update_types: list[str] = []
    async for update_type, _data in orchestrator.run_experiments_streaming():
        update_types.append(update_type)
    assert "results" in update_types
    assert "experiment" in update_types
