"""Tests for concurrent multi-agent fault injection."""

from pathlib import Path

import pytest

from rogue.injectors.base_injector import InjectorId
from rogue.resilience.models import ArchitectureId
from rogue.resilience.orchestrator import ResilienceOrchestrator

FIXTURE = Path(__file__).parent / "fixtures" / "resilience_multi_agent_entrypoint.py"


@pytest.mark.asyncio
async def test_concurrent_injection_records_multiple_targets() -> None:
    orchestrator = ResilienceOrchestrator(
        injectors=[InjectorId.POLICY_VIOLATION],
        python_entrypoint_file=str(FIXTURE),
        architecture=ArchitectureId.HIERARCHICAL,
        target_agent_id="worker-1",
        concurrent_target_agent_ids=["worker-1", "worker-2"],
        experiments_per_injector=1,
        use_heuristics=True,
    )
    results = await orchestrator.run_experiments()
    assert results.total_experiments == 1
    trace = results.experiments[0].trace
    injection_events = [e for e in trace.events if e.event_type.value == "injection"]
    assert injection_events
    assert injection_events[0].payload.get("concurrent_targets") == ["worker-1", "worker-2"]
