"""Integration tests for multi-agent resilience orchestration."""

from pathlib import Path

import pytest

from rogue.injectors.base_injector import InjectorId
from rogue.resilience.models import ArchitectureId, ResilienceMetricId
from rogue.resilience.orchestrator import ResilienceOrchestrator

SINGLE_AGENT = Path(__file__).parent / "fixtures" / "resilience_test_agent.py"
MULTI_AGENT = Path(__file__).parent / "fixtures" / "resilience_multi_agent_entrypoint.py"


@pytest.mark.asyncio
async def test_single_agent_phase1_still_passes() -> None:
    """Phase 1 single-agent behavior remains unchanged."""
    orchestrator = ResilienceOrchestrator(
        injectors=[InjectorId.POLICY_VIOLATION],
        python_entrypoint_file=str(SINGLE_AGENT),
        architecture=ArchitectureId.SINGLE_AGENT,
        use_heuristics=True,
    )
    results = await orchestrator.run_experiments()
    assert results.total_experiments == 1
    metric_ids = {m.metric_id for m in results.experiments[0].metrics}
    assert metric_ids == {
        ResilienceMetricId.DETECTION,
        ResilienceMetricId.CONTAINMENT,
        ResilienceMetricId.RECOVERY,
    }


@pytest.mark.asyncio
async def test_hierarchical_multi_agent_experiment() -> None:
    orchestrator = ResilienceOrchestrator(
        injectors=[InjectorId.POLICY_VIOLATION],
        python_entrypoint_file=str(MULTI_AGENT),
        architecture=ArchitectureId.HIERARCHICAL,
        target_agent_id="worker-1",
        use_heuristics=True,
    )
    results = await orchestrator.run_experiments()
    assert results.total_experiments == 1
    experiment = results.experiments[0]
    metric_ids = {m.metric_id for m in experiment.metrics}
    assert ResilienceMetricId.CASCADING_FAILURE in metric_ids
    assert ResilienceMetricId.SYSTEM_DEGRADATION in metric_ids
    assert any(event.agent_id == "supervisor" for event in experiment.trace.events)
