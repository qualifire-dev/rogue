"""Run LangGraph checkpoint recovery resilience demo."""

import asyncio
from pathlib import Path

from rogue.injectors.base_injector import InjectorId
from rogue.resilience.orchestrator import ResilienceOrchestrator

ENTRYPOINT = Path(__file__).parent / "python_entrypoint.py"


async def main() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("lg_entry", ENTRYPOINT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    adapter = module.get_checkpoint_adapter()
    orchestrator = ResilienceOrchestrator(
        injectors=[InjectorId.POLICY_VIOLATION],
        python_entrypoint_file=str(ENTRYPOINT),
        business_context="LangGraph agent with checkpoint recovery",
        use_heuristics=True,
        enable_checkpoint_recovery=True,
        checkpoint_adapter=adapter,
        checkpoint_thread_id="resilience-recovery-demo",
    )
    results = await orchestrator.run_experiments()
    print(f"Overall score: {results.overall_score}")
    print(f"Recovery rate: {results.recovery_rate:.0%}")


if __name__ == "__main__":
    asyncio.run(main())
