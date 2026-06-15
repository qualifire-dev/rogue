# Multi-agent hierarchical resilience example

Supervisor + two workers for Rogue Resilience chaos experiments.

## Run the demo

```bash
uv sync --all-groups
uv run python -m examples.multi_agent_hierarchical.run_resilience_demo
```

## Entrypoint

`python_entrypoint.py` exposes `call_agent(messages, context_id, agent_id, **kwargs)`
for hierarchical routing. The supervisor detects rogue output broadcast from workers.

## Via orchestrator API

```python
from rogue.resilience.models import ArchitectureId
from rogue.resilience.orchestrator import ResilienceOrchestrator

orchestrator = ResilienceOrchestrator(
    injectors=["policy_violation"],
    python_entrypoint_file="examples/multi_agent_hierarchical/python_entrypoint.py",
    architecture=ArchitectureId.HIERARCHICAL,
    target_agent_id="worker-1",
    use_heuristics=True,
)
results = await orchestrator.run_experiments()
```
