# Rogue Resilience

Rogue Resilience is an official extension for [Qualifire Rogue](https://github.com/qualifire-dev/rogue) that benchmarks multi-agent systems against suddenly rogue or malicious agents. It focuses on fault injection, detection, containment, correction, and recovery metrics.

Phase 1 provides single-agent injection via the **Python protocol**, five built-in injectors, core resilience metrics, a REST API, and programmatic orchestration.

## Installation

Rogue Resilience ships inside the main `rogue-ai` package. Install Rogue as usual:

```bash
git clone https://github.com/qualifire-dev/rogue.git
cd rogue
uv sync --all-groups
```

LangGraph is **optional** and only required for checkpoint replay features planned in Phase 2:

```bash
uv sync --group examples   # includes langgraph
```

No changes to existing Policy or Red Team workflows are required.

## Quickstart (Phase 1)

### 1. Prepare a Python agent entrypoint

Your agent must expose a `call_agent(messages, context_id=None, **kwargs)` function (same convention as Policy evaluation):

```python
# my_agent.py
def call_agent(messages, context_id=None, **kwargs):
    if kwargs.get("resilience_injection"):
        return "Sorry, I cannot comply with that request due to store policy."
    return "Hello! How can I help?"
```

See `examples/python_entrypoint_stub.py` for a full template. The test fixture at `rogue/tests/fixtures/resilience_test_agent.py` is a working reference.

### 2. Run a full experiment via the SDK (recommended)

Start the Rogue server in one terminal:

```bash
uv run rogue-ai web
```

Run a complete experiment from Python in another terminal:

```python
import asyncio
from pathlib import Path

from rogue_sdk import RogueSDK, RogueClientConfig
from rogue_sdk.types import (
    EvaluationStatus,
    Protocol,
    ResilienceConfig,
    ResilienceRequest,
)

AGENT = Path("rogue/tests/fixtures/resilience_test_agent.py").resolve()

async def main() -> None:
    async with RogueSDK(RogueClientConfig(base_url="http://127.0.0.1:8000")) as sdk:
        response = await sdk.create_resilience_job(
            ResilienceRequest(
                resilience_config=ResilienceConfig(
                    injectors=["policy_violation", "tool_misuse"],
                    experiments_per_injector=1,
                    use_heuristics=True,
                ),
                evaluated_agent_protocol=Protocol.PYTHON,
                python_entrypoint_file=str(AGENT),
                judge_llm="openai/gpt-4o-mini",
                business_context="T-shirt store with fixed pricing",
            ),
        )
        print(f"Job created: {response.job_id}")

        job = await sdk.wait_for_resilience_job(response.job_id, max_wait_time=120)
        print(f"Status: {job.status}")

        if job.status == EvaluationStatus.COMPLETED and job.results:
            print(f"Overall score: {job.results.get('overall_score')}")
            print(f"Detection rate: {job.results.get('detection_rate')}")
            for exp in job.results.get("experiments", []):
                print(f"  - {exp['injector_id']}: score={exp['composite_score']}")

asyncio.run(main())
```

### 3. Run a full experiment via curl (CLI)

With the server running (`uv run rogue-ai web`):

```bash
# Create job
JOB=$(curl -s -X POST http://127.0.0.1:8000/api/v1/resilience \
  -H "Content-Type: application/json" \
  -d "{
    \"resilience_config\": {
      \"injectors\": [\"policy_violation\"],
      \"experiments_per_injector\": 1,
      \"use_heuristics\": true
    },
    \"evaluated_agent_protocol\": \"python\",
    \"python_entrypoint_file\": \"$(pwd)/rogue/tests/fixtures/resilience_test_agent.py\",
    \"judge_llm\": \"openai/gpt-4o-mini\",
    \"business_context\": \"T-shirt store\"
  }" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")

echo "Job ID: $JOB"

# Poll until complete
until curl -s "http://127.0.0.1:8000/api/v1/resilience/$JOB" \
  | python3 -c "import sys,json; s=json.load(sys.stdin)['status']; print(s); exit(0 if s in ('completed','failed','cancelled') else 1)"; do
  sleep 2
done

# Print results
curl -s "http://127.0.0.1:8000/api/v1/resilience/$JOB" | python3 -m json.tool
```

### 4. Run experiments in-process (no server)

For local development and CI, call the orchestrator directly:

```python
import asyncio
from pathlib import Path

from rogue.injectors.base_injector import InjectorId
from rogue.resilience.orchestrator import ResilienceOrchestrator

AGENT = Path("rogue/tests/fixtures/resilience_test_agent.py")

async def main():
    orchestrator = ResilienceOrchestrator(
        injectors=[InjectorId.POLICY_VIOLATION, InjectorId.TOOL_MISUSE],
        python_entrypoint_file=str(AGENT),
        business_context="Customer support agent",
        use_heuristics=True,
    )
    results = await orchestrator.run_experiments()
    print(f"Overall score: {results.overall_score}")
    print(f"Detection rate: {results.detection_rate:.0%}")

asyncio.run(main())
```

## Built-in injectors

| ID | Strategy |
|----|----------|
| `tool_misuse` | Unauthorized or malformed tool calls |
| `hallucination_spamming` | High-volume fabricated output |
| `goal_conflict` | Adversarial sub-goals |
| `policy_violation` | Deliberate business-rule breaches |
| `action_spam` | Rapid-fire messages and actions |

List injectors in Python:

```python
from rogue.injectors.registry import list_injectors
for item in list_injectors():
    print(item.id, item.name)
```

## Metrics (Phase 1)

| Metric | Description |
|--------|-------------|
| **Detection** | Was rogue behavior flagged? (rate + latency) |
| **Containment** | Was harm prevented before downstream impact? |
| **Recovery** | Did the system return to a healthy state after teardown? |

Metrics use deterministic heuristics by default (`use_heuristics=True`). Set `use_heuristics=False` and provide a `judge_llm` for semantic evaluation.

## Module layout

```
rogue/injectors/          # Fault injection strategies
rogue/resilience/         # Models, metrics, orchestrator
rogue/server/api/resilience.py
rogue/server/services/resilience_service.py
docs/resilience/PLAN.md   # Full architecture and roadmap
```

## Tests

```bash
uv run pytest rogue/tests/test_injectors.py \
             rogue/tests/test_resilience_metrics.py \
             rogue/tests/test_resilience_orchestrator.py -v
```

## Roadmap

See [PLAN.md](./PLAN.md) for the full phased roadmap. Phase 2 adds multi-agent architectures, LangGraph checkpoint replay, and dashboard visualizations.

## Related documentation

- [Architecture & roadmap](./PLAN.md)
- [Rogue AGENTS.md](../../AGENTS.md) — build, lint, and test commands
