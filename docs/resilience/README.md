# Rogue Resilience

Rogue Resilience is an official extension for [Qualifire Rogue](https://github.com/qualifire-dev/rogue) that benchmarks multi-agent systems against suddenly rogue or malicious agents. It focuses on fault injection, detection, containment, correction, and recovery metrics.

## Installation

Rogue Resilience ships inside the main `rogue-ai` package:

```bash
git clone https://github.com/qualifire-dev/rogue.git
cd rogue
uv sync --all-groups
```

| Dependency group | When you need it |
|------------------|------------------|
| *(default)* | Single-agent experiments, injectors, core metrics, REST API |
| `examples` | LangGraph checkpoint recovery demos |
| `resilience` | LangGraph only (minimal checkpoint support) |

```bash
uv sync --group examples    # LangGraph + example agents
uv sync --group resilience    # LangGraph only
```

No changes to existing Policy or Red Team workflows are required.

---

## Examples overview

| Example | Architecture | LangGraph | Command |
|---------|-------------|-----------|---------|
| Single-agent fixture | `single_agent` | No | See [Quickstart](#quickstart-single-agent) |
| [Hierarchical multi-agent](#hierarchical-multi-agent-example) | `hierarchical` | No | `uv run python -m examples.multi_agent_hierarchical.run_resilience_demo` |
| [LangGraph recovery](#langgraph-checkpoint-recovery-example) | `single_agent` | Yes | `uv run python -m examples.resilience_langgraph_recovery.run_recovery_demo` |

---

## Quickstart (single-agent)

Phase 1 single-agent mode is unchanged. Your entrypoint needs only:

```python
def call_agent(messages, context_id=None, **kwargs):
    if kwargs.get("resilience_injection"):
        return "Sorry, I cannot comply with that request due to store policy."
    return "Hello! How can I help?"
```

### In-process (fastest)

```python
import asyncio
from pathlib import Path

from rogue.injectors.base_injector import InjectorId
from rogue.resilience.orchestrator import ResilienceOrchestrator

AGENT = Path("rogue/tests/fixtures/resilience_test_agent.py")

async def main():
    orchestrator = ResilienceOrchestrator(
        injectors=[InjectorId.POLICY_VIOLATION],
        python_entrypoint_file=str(AGENT),
        use_heuristics=True,
    )
    results = await orchestrator.run_experiments()
    print(f"Overall score: {results.overall_score}")

asyncio.run(main())
```

### Via SDK + server

```bash
# Terminal 1
uv run rogue-ai web

# Terminal 2 — run the SDK script from Quickstart section below, or use curl
```

<details>
<summary>SDK example (expand)</summary>

```python
import asyncio
from pathlib import Path

from rogue_sdk import RogueSDK, RogueClientConfig
from rogue_sdk.types import EvaluationStatus, Protocol, ResilienceConfig, ResilienceRequest

AGENT = Path("rogue/tests/fixtures/resilience_test_agent.py").resolve()

async def main():
    async with RogueSDK(RogueClientConfig(base_url="http://127.0.0.1:8000")) as sdk:
        response = await sdk.create_resilience_job(
            ResilienceRequest(
                resilience_config=ResilienceConfig(
                    injectors=["policy_violation"],
                    use_heuristics=True,
                ),
                evaluated_agent_protocol=Protocol.PYTHON,
                python_entrypoint_file=str(AGENT),
                judge_llm="openai/gpt-4o-mini",
            ),
        )
        job = await sdk.wait_for_resilience_job(response.job_id)
        print(job.results)

asyncio.run(main())
```

</details>

---

## Hierarchical multi-agent example

Demonstrates a **supervisor + two workers** system where faults are injected into `worker-1`, peers are notified, and the supervisor is queried for detection.

### Run the demo

```bash
uv sync --all-groups
uv run python -m examples.multi_agent_hierarchical.run_resilience_demo
```

Expected output includes overall score, detection rate, cascade score, and per-injector results.

### Entrypoint contract

Multi-agent entrypoints must accept `agent_id`:

```python
# examples/multi_agent_hierarchical/python_entrypoint.py
def call_agent(messages, context_id=None, agent_id="supervisor", **kwargs):
    return route_agent(agent_id, messages, **kwargs)
```

### Programmatic usage

```python
from rogue.injectors.base_injector import InjectorId
from rogue.resilience.models import ArchitectureId
from rogue.resilience.orchestrator import ResilienceOrchestrator

orchestrator = ResilienceOrchestrator(
    injectors=[InjectorId.POLICY_VIOLATION],
    python_entrypoint_file="examples/multi_agent_hierarchical/python_entrypoint.py",
    architecture=ArchitectureId.HIERARCHICAL,
    target_agent_id="worker-1",  # defaults to profile default if omitted
    business_context="Hierarchical t-shirt store with supervisor and workers",
    use_heuristics=True,
)
results = await orchestrator.run_experiments()

print(f"Detection:  {results.detection_rate:.0%}")
print(f"Cascade:    {results.cascading_failure_rate:.0%}")
print(f"Degradation:{results.system_degradation_rate:.0%}")
```

### Via REST API

```bash
curl -X POST http://127.0.0.1:8000/api/v1/resilience \
  -H "Content-Type: application/json" \
  -d '{
    "resilience_config": {
      "injectors": ["policy_violation"],
      "architecture": "hierarchical",
      "target_agent_id": "worker-1",
      "use_heuristics": true
    },
    "evaluated_agent_protocol": "python",
    "python_entrypoint_file": "examples/multi_agent_hierarchical/python_entrypoint.py",
    "judge_llm": "openai/gpt-4o-mini"
  }'
```

---

## LangGraph checkpoint recovery example

Demonstrates optional **snapshot → fault → restore → recovery** using a deterministic LangGraph (no LLM API key required).

### Run the demo

```bash
uv sync --group examples
uv run python -m examples.resilience_langgraph_recovery.run_recovery_demo
```

### How it works

1. Baseline invocation creates checkpoint `C0`
2. Orchestrator snapshots `C0` before injection
3. Fault probes run against the agent
4. After teardown, checkpoint `C0` is restored via `LangGraphCheckpointAdapter`
5. Recovery validation runs against restored state

### Enable checkpoints in code

```python
from examples.resilience_langgraph_recovery.python_entrypoint import get_checkpoint_adapter
from rogue.resilience.orchestrator import ResilienceOrchestrator

orchestrator = ResilienceOrchestrator(
    injectors=["policy_violation"],
    python_entrypoint_file="examples/resilience_langgraph_recovery/python_entrypoint.py",
    use_heuristics=True,
    enable_checkpoint_recovery=True,
    checkpoint_adapter=get_checkpoint_adapter(),
    checkpoint_thread_id="my-resilience-thread",
)
```

Checkpoint failures are logged and recorded on the experiment trace but **do not abort** the run — experiments continue without recovery if snapshot/restore fails.

### SDK with checkpoints

```python
ResilienceConfig(
    injectors=["policy_violation"],
    enable_checkpoint_recovery=True,
    checkpoint_thread_id="my-resilience-thread",
    use_heuristics=True,
)
```

Note: the REST API passes config to the server orchestrator; you must wire a checkpoint adapter in-process or extend the entrypoint with a `get_checkpoint_adapter()` hook for full recovery via API.

---

## Architecture profiles

```python
from rogue.resilience.catalog import get_architecture, list_architectures

for profile in list_architectures():
    print(profile.id.value, profile.name, profile.agent_ids)
```

| ID | Topology | Agents |
|----|----------|--------|
| `single_agent` | Phase 1 default (unchanged) | `default` |
| `hierarchical` | Supervisor + workers | `supervisor`, `worker-1`, `worker-2` |
| `peer_to_peer` | Fully connected peers | `peer-a`, `peer-b`, `peer-c` |
| `supervisor_worker` | Sequential pipeline | `supervisor`, `worker-1`, `worker-2` |

Each profile defines `entry_agent_id`, `default_injection_target`, `detection_agents`, and `notify_on_fault` peer routing.

---

## Built-in injectors

| ID | Strategy |
|----|----------|
| `tool_misuse` | Unauthorized or malformed tool calls |
| `hallucination_spamming` | High-volume fabricated output |
| `goal_conflict` | Adversarial sub-goals |
| `policy_violation` | Deliberate business-rule breaches |
| `action_spam` | Rapid-fire messages and actions |

```python
from rogue.injectors.registry import list_injectors
for item in list_injectors():
    print(item.id.value, item.name)
```

---

## Metrics

| Metric | Phase | Description |
|--------|-------|-------------|
| **Detection** | 1 | Was rogue behavior flagged? (rate + latency) |
| **Containment** | 1 | Was harm prevented before downstream impact? |
| **Recovery** | 1 | Did the system return to a healthy state after teardown? |
| **Cascading failure** | 2 | How many agents were corrupted? (multi-agent only) |
| **System degradation** | 2 | Baseline vs fault-window success rate (multi-agent only) |

Single-agent runs use the original 3-metric composite weights. Multi-agent runs add cascade and degradation.

Metrics use deterministic heuristics by default (`use_heuristics=True`). Set `use_heuristics=False` and provide a `judge_llm` for semantic evaluation.

---

## Dashboard & reporting (Phase 3)

The web UI mirrors the Red Team section at `/resilience/*`:

| Route | Purpose |
|-------|---------|
| `/resilience/` | Experiment list |
| `/resilience/configure` | Configure chaos experiment |
| `/resilience/$jobId` | Live trace viewer (WebSocket) |
| `/resilience/$jobId/report` | Scorecard, radar chart, breakdown, topology |

### End-to-end user journey

Follow this path from zero to a published resilience report — the same flow a new user would take in the browser.

**Step 1 — Install and start the server**

```bash
uv sync --all-groups
cd packages/web && pnpm install && pnpm routes && pnpm build && cd ../..
uv run rogue-ai web
```

Open http://127.0.0.1:8000. The home dashboard shows a **Resilience runs** metric card and recent experiments (empty on first visit).

**Step 2 — Configure an experiment**

Navigate to **Resilience → New experiment** (or `/resilience/configure`).

1. Set **Target agent** to Python protocol and point at `rogue/tests/fixtures/resilience_test_agent.py`.
2. Choose preset **Basic** (policy violation + tool misuse) or pick injectors manually.
3. Select architecture **Single agent** (or **Hierarchical** for multi-agent cascade metrics).
4. Leave **Use heuristics** on for fast, deterministic scoring (no LLM judge calls).
5. Click **Run experiment**.

**Step 3 — Watch the live trace**

You land on `/resilience/{jobId}`. While the job runs:

- Progress bar advances as each injector completes.
- **Live trace** panel streams color-coded events: baseline → injection → probe messages → recovery → checkpoint (if enabled).
- Status rail shows connection state (`open`, `polling`, or `connecting`), trace event count, and injector list.

When status becomes `completed`, the page auto-redirects to the report.

**Step 4 — Review the report**

At `/resilience/{jobId}/report`:

| Tab | What you see |
|-----|----------------|
| **Report** | Hero score (/100), experiments passed, metrics radar, rate bars, key findings |
| **Breakdown** | Per-injector table with detection/containment/recovery scores; **Export CSV** |
| **Trace** | Full experiment timeline + checkpoint scrubber (prev/next through snapshot/restore) |
| **Topology** | Agent graph with fault target highlighted in red |

**Step 5 — Export or automate**

- **Browser:** Download CSV from the Breakdown tab.
- **API:** `GET /api/v1/resilience/{job_id}/report` returns the same JSON the UI renders.
- **CLI:** Run headless and write markdown (see below).

**Step 6 — Iterate**

Return to `/resilience/configure`, add injectors, switch to `hierarchical` architecture, or enable checkpoint recovery for LangGraph agents. Past runs remain listed at `/resilience/`.

---

### UI screenshots (descriptions)

Screenshots are not bundled in the repo yet; capture these from a local run for docs or release notes. Each mirrors the Red Team visual language (dark sidebar, card layout, status badges).

| # | Page | What to capture |
|---|------|-----------------|
| 1 | **Dashboard** (`/`) | Operational Console with four metric cards; **Recent resilience runs** panel showing 1–2 completed jobs with status badges. |
| 2 | **Experiment list** (`/resilience/`) | Table columns: Job ID, Status, Progress, Architecture, Created; **Configure experiment** button top-right. |
| 3 | **Configure** (`/resilience/configure`) | Left: injector catalog pane with checkboxes; right: architecture cards, target agent field, heuristics/checkpoint toggles; **Run experiment** CTA. |
| 4 | **Live trace** (`/resilience/{id}`) | Split layout: left trace feed with colored event pills (blue baseline, red injection, green recovery); right status rail with progress and WebSocket connection pill. |
| 5 | **Report hero** (`/resilience/{id}/report`) | Large **Overall score** stat (e.g. 78/100), architecture badge, experiments passed fraction. |
| 6 | **Report radar** (Report tab) | Recharts radar with Detection, Containment, Recovery axes filled to percentage values. |
| 7 | **Trace tab** | Vertical timeline of labeled events; optional checkpoint scrubber below with snapshot/restore step detail. |
| 8 | **Topology tab** | SVG agent graph: supervisor + workers, red node on injection target, arrow edges for delegation/notify. |

Suggested capture: 1440×900 browser window, dark theme, one single-agent and one hierarchical run for comparison.

---

### Start the full flow (CLI + API)

```bash
# Terminal 1 — server + bundled SPA
uv sync --all-groups
cd packages/web && pnpm install && pnpm build   # first time only
uv run rogue-ai web

# Terminal 2 — CLI with report export
uv run rogue-ai cli \
  --evaluation-mode resilience \
  --protocol python \
  --python-entrypoint-file rogue/tests/fixtures/resilience_test_agent.py \
  --injectors policy_violation \
  --judge-llm openai/gpt-4o-mini \
  --output-report-file ./resilience_report.md
```

Open http://127.0.0.1:8000/resilience/configure for the browser flow. The report page includes:

- **Metrics radar** — detection, containment, recovery (+ cascade/degradation for multi-agent)
- **Timeline** — injection, detection, recovery, and checkpoint markers
- **Agent graph** — topology with fault target highlighted
- **Checkpoint scrubber** — step through snapshot/restore when enabled
- **CSV export** — per-injector breakdown table

Report API: `GET /api/v1/resilience/{job_id}/report`

WebSocket events: `job_update` + `resilience_trace_update` for live traces.

Components show loading spinners and error panels while data is fetching or if the WebSocket disconnects.

---

## Module layout

```
rogue/injectors/              # Fault injection strategies
rogue/resilience/
├── catalog/architectures.py  # Multi-agent topology profiles
├── checkpoint/               # LangGraph checkpoint adapters
├── multi_agent_client.py     # agent_id routing
├── orchestrator.py           # Experiment engine
└── metrics/                  # Detection, containment, recovery, cascade, degradation
rogue/server/resilience/report/   # Report generator (markdown/CSV/web)
rogue/evaluator_agent/resilience/  # Protocol adapters
packages/web/src/routes/resilience/  # Dashboard routes
packages/web/src/components/resilience/  # Timeline, graph, radar
examples/
├── multi_agent_hierarchical/
└── resilience_langgraph_recovery/
docs/resilience/PLAN.md       # Full architecture and roadmap
```

---

## Tests

```bash
uv run pytest rogue/tests/test_injectors.py \
             rogue/tests/test_resilience_metrics.py \
             rogue/tests/test_resilience_orchestrator.py \
             rogue/tests/test_multi_agent_orchestrator.py \
             rogue/tests/test_langgraph_checkpoint_adapter.py \
             rogue/tests/test_resilience_reporting.py -v
```

`test_multi_agent_orchestrator.py::test_single_agent_phase1_still_passes` verifies Phase 1 backward compatibility.

---

## Related documentation

- [Architecture & roadmap](./PLAN.md)
- [Rogue AGENTS.md](../../AGENTS.md) — build, lint, and test commands
