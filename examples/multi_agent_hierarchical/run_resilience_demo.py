"""Run a hierarchical multi-agent resilience demo."""

import asyncio
from pathlib import Path

from rogue.injectors.base_injector import InjectorId
from rogue.resilience.models import ArchitectureId
from rogue.resilience.orchestrator import ResilienceOrchestrator

ENTRYPOINT = Path(__file__).parent / "python_entrypoint.py"


async def main() -> None:
    orchestrator = ResilienceOrchestrator(
        injectors=[InjectorId.POLICY_VIOLATION],
        python_entrypoint_file=str(ENTRYPOINT),
        architecture=ArchitectureId.HIERARCHICAL,
        target_agent_id="worker-1",
        business_context="Hierarchical t-shirt store with supervisor and workers",
        use_heuristics=True,
    )
    results = await orchestrator.run_experiments()
    print(f"Architecture: {results.metadata.get('architecture')}")
    print(f"Overall score: {results.overall_score}")
    print(f"Detection rate: {results.detection_rate:.0%}")
    print(f"Cascade score: {results.cascading_failure_rate:.0%}")
    for experiment in results.experiments:
        print(
            f"  {experiment.injector_id.value}: "
            f"score={experiment.composite_score} passed={experiment.passed}",
        )


if __name__ == "__main__":
    asyncio.run(main())
