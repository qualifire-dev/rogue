# Injectors — catalog, plugins, and premium strategies

Rogue Resilience fault injectors live in `rogue/injectors/`. Each injector arms at a controlled point in an experiment and emits probe messages that exercise detection, containment, and recovery.

## Built-in injectors

| ID | Name | Premium |
|----|------|---------|
| `tool_misuse` | Tool misuse | No |
| `hallucination_spamming` | Hallucination spamming | No |
| `goal_conflict` | Goal conflict | No |
| `policy_violation` | Policy violation | No |
| `action_spam` | Action spam | No |
| `gradual_goal_drift` | Gradual goal drift | Yes (local) |
| `deckard_adaptive_injection` | Deckard adaptive | Yes (Deckard) |

List via API: `GET /api/v1/resilience/injectors/catalog`

## Custom injector plugin API

### File-based plugin

Create a module with `INJECTOR_CLASS`:

```python
# my_injector.py
from rogue.injectors.base_injector import BaseInjector, InjectionContext, InjectionResult

class MyInjector(BaseInjector):
    id = "my_injector"
    name = "My Injector"
    description = "Custom chaos strategy"

    async def inject(self, target_agent_id, context):
        self._armed = True
        return InjectionResult(
            injector_id=self.id,
            target_agent_id=target_agent_id,
            probe_messages=self.get_probe_messages(),
        )

    def get_probe_messages(self):
        return ["probe message"]

INJECTOR_CLASS = MyInjector
```

Load at runtime:

```python
from rogue.injectors.plugins import load_injector_plugin

load_injector_plugin("path/to/my_injector.py")
```

Or pass paths in job config:

```python
ResilienceConfig(
    injectors=["my_injector", "policy_violation"],
    custom_injector_plugins=["path/to/my_injector.py"],
)
```

### Programmatic registration

```python
from rogue.injectors.plugins import register_injector

register_injector(
    "my_injector",
    name="My Injector",
    description="...",
    factory=MyInjector,
)
```

See [examples/custom_injector_plugin/example_injector.py](../../examples/custom_injector_plugin/example_injector.py).

## Concurrent multi-injection

Fault multiple agents simultaneously in one experiment:

```python
ResilienceConfig(
    architecture="hierarchical",
    injectors=["policy_violation"],
    target_agent_id="worker-1",
    concurrent_target_agent_ids=["worker-1", "worker-2"],
)
```

The orchestrator runs parallel injection + probe loops and records `concurrent_targets` on the trace.

## Premium / Deckard injectors

Premium strategies follow the Red Team `PREMIUM_ATTACKS` pattern:

- **Local premium** (e.g. `gradual_goal_drift`) ships in-repo; no API key required.
- **Deckard premium** (`deckard_adaptive_injection`) requires `ROGUE_SECURITY_API_KEY` for cloud-generated probes (metadata registered; live fetch is a future enhancement).

## CI score gate

Set a minimum acceptable score on a job:

```python
ResilienceConfig(
    injectors=["policy_violation"],
    min_resilience_score=60.0,
)
```

Jobs scoring below the threshold are marked `failed`. The GitHub workflow [`.github/workflows/resilience-gate.yml`](../../.github/workflows/resilience-gate.yml) runs the same check in CI.

## Robustness vs Resilience

| Mode | What it tests |
|------|----------------|
| **Red Team (Robustness)** | External adversarial attacks on your agent |
| **Resilience** | Internal faults — when an agent in your system goes rogue |

Both are available in the Rogue web UI under separate sidebar sections.
