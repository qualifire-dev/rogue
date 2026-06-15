# Rogue — AI Agent Evaluator, Red Team & Resilience Platform

![](https://pixel.qualifire.ai/api/record/rogue)

<div align="center">

<a href="https://trendshift.io/repositories/15191" target="_blank"><img src="https://trendshift.io/api/badge/repositories/15191" alt="qualifire-dev%2Frogue | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

![Tests](https://github.com/qualifire-dev/rogue/actions/workflows/test.yml/badge.svg?branch=main)

[![Resilience](https://img.shields.io/badge/Rogue%20Resilience-chaos%20testing-8B5CF6?style=flat-square)](./docs/resilience/README.md)
[![Multi-agent](https://img.shields.io/badge/multi--agent-hierarchical%20%7C%20P2P-3B82F6?style=flat-square)](./docs/resilience/README.md#architecture-profiles)
[![Dashboard](https://img.shields.io/badge/web%20UI-%2Fresilience-10B981?style=flat-square)](./docs/resilience/README.md#dashboard--reporting-phase-3)

<img src="./freddy-rogue.png" width="200"/>

**Stress-test your AI agents before attackers do — and before internal faults cascade.**

[Discord Community](https://discord.gg/EUfAt7ZDeK) · [Quick Start](#-quick-start) · [Rogue Resilience](#-rogue-resilience) · [Documentation](./docs/)

</div>

---

## Three Ways to Harden Your Agent

<table>
<tr>
<td width="33%" valign="top">

### 🎯 Automatic Evaluation

Test your agent against **business policies** and expected behaviors.

- Define scenarios & expected outcomes
- Verify compliance with business rules
- Watch live conversations as Rogue probes your agent
- Get detailed pass/fail reports with reasoning

**Best for:** Regression testing, behavior validation, policy compliance

</td>
<td width="33%" valign="top">

### 🔴 Red Teaming

Simulate **adversarial attacks** to find security vulnerabilities.

- 75+ vulnerabilities across 12 security categories
- 20 attack techniques (encoding, social engineering, injection)
- CVSS-based risk scoring
- 8 compliance frameworks (OWASP, MITRE, NIST, GDPR, EU AI Act)

**Best for:** Security audits, penetration testing, compliance reporting

</td>
<td width="33%" valign="top">

### ⚡ Rogue Resilience

Benchmark **internal fault tolerance** when an agent goes rogue.

- 5 fault injectors (tool misuse, policy violation, goal conflict, …)
- Multi-agent architectures (hierarchical, peer-to-peer)
- Detection · containment · recovery · cascade · degradation metrics
- Live trace dashboard + markdown/CSV reports

**Best for:** Multi-agent chaos testing, supervisor/worker resilience, LangGraph recovery

[→ Full Resilience docs](./docs/resilience/README.md)

</td>
</tr>
</table>

---

## ⚡ Rogue Resilience

> **Red Team** tests external attackers. **Resilience** tests internal faults — when a worker agent suddenly misbehaves, can your system detect, contain, and recover?

| Quick link | Description |
|------------|-------------|
| [Resilience README](./docs/resilience/README.md) | Install, examples, metrics, dashboard |
| [Architecture & roadmap](./docs/resilience/PLAN.md) | Full design and phased delivery |
| Web UI | `http://localhost:8000/resilience/configure` (after `uv run rogue-ai web`) |
| CLI | `uv run rogue-ai cli --evaluation-mode resilience --protocol python …` |

```bash
# Start server + dashboard
uv sync --all-groups && uv run rogue-ai web

# Run a chaos experiment from CLI (writes resilience_report.md)
uv run rogue-ai cli \
  --evaluation-mode resilience \
  --protocol python \
  --python-entrypoint-file rogue/tests/fixtures/resilience_test_agent.py \
  --injectors policy_violation \
  --judge-llm openai/gpt-4o-mini
```

**What's included:** fault injectors · multi-agent profiles · LangGraph checkpoint adapters · REST API · WebSocket live traces · scorecard report with radar chart, timeline, agent graph, and CSV export.

---

## Architecture

Rogue operates on a **client-server architecture** with multiple interfaces:

| Component  | Description                                 |
| ---------- | ------------------------------------------- |
| **Server** | Core evaluation & red team logic            |
| **TUI**    | Modern terminal interface (Go + Bubble Tea) |
| **CLI**    | Non-interactive mode for CI/CD pipelines    |

https://github.com/user-attachments/assets/b5c04772-6916-4aab-825b-6a7476d77787

### Supported Protocols

| Protocol   | Transport            | Description                                                                        |
| ---------- | -------------------- | ---------------------------------------------------------------------------------- |
| **A2A**    | HTTP                 | [Google's Agent-to-Agent](https://a2a-protocol.org/latest/) protocol               |
| **MCP**    | SSE, STREAMABLE_HTTP | [Model Context Protocol](https://modelcontextprotocol.io/) via `send_message` tool |
| **Python** | —                    | Direct Python function calls (no network protocol)                                 |

See examples in [`examples/`](./examples/) for reference implementations.

#### Python Entrypoint

For agents implemented as Python functions without A2A or MCP:

1. Create a Python file with a `call_agent` function:

```python
def call_agent(messages: list[dict]) -> str:
    """
    Process conversation and return response.

    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."}

    Returns:
        Agent's response as a string
    """
    # Your agent logic here
    latest = messages[-1]["content"]
    return f"Response to: {latest}"
```

2. Run Rogue with Python protocol:

```bash
uvx rogue-ai cli \
  --protocol python \
  --python-entrypoint-file ./my_agent.py \
  --judge-llm openai/gpt-4o-mini
```

Or via TUI: select "Python" as the protocol and enter the file path.

See [`examples/python_entrypoint_stub.py`](./examples/python_entrypoint_stub.py) for a complete example.

---

## 🔥 Quick Start

### Prerequisites

- `uvx` — [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.10+
- LLM API key (OpenAI, Anthropic, or Google)

### Installation

```bash
# TUI (recommended)
uvx rogue-ai

# CLI / CI/CD
uvx rogue-ai cli
```

### Try It With the Example Agent

```bash
# All-in-one: starts both Rogue and a sample T-shirt store agent
uvx rogue-ai --example=tshirt_store
```

Configure in the UI:

- **Agent URL**: `http://localhost:10001`
- **Mode**: Choose `Automatic Evaluation` or `Red Teaming`

---

## Running Modes

| Mode    | Command               | Description             |
| ------- | --------------------- | ----------------------- |
| Default | `uvx rogue-ai`        | Server + TUI            |
| Server  | `uvx rogue-ai server` | Backend only            |
| TUI     | `uvx rogue-ai tui`    | Terminal client         |
| CLI     | `uvx rogue-ai cli`    | Non-interactive (CI/CD) |

### Server Options

```bash
uvx rogue-ai server --host 0.0.0.0 --port 8000 --debug
```

### CLI Options

```bash
uvx rogue-ai cli \
  --evaluated-agent-url http://localhost:10001 \
  --judge-llm openai/gpt-4o-mini \
  --business-context-file ./.rogue/business_context.md
```

| Option                   | Description                                 |
| ------------------------ | ------------------------------------------- |
| `--config-file`          | Path to config JSON                         |
| `--evaluated-agent-url`  | Agent endpoint (required)                   |
| `--judge-llm`            | LLM for evaluation (required)               |
| `--business-context`     | Context string or `--business-context-file` |
| `--input-scenarios-file` | Scenarios JSON                              |
| `--output-report-file`   | Report output path                          |

---

## Red Teaming

### Scan Types

| Type       | Vulnerabilities | Attacks       | Time       |
| ---------- | --------------- | ------------- | ---------- |
| **Basic**  | 5 curated       | 6             | ~2-3 min   |
| **Full**   | 75+             | 40+           | ~30-45 min |
| **Custom** | User-selected   | User-selected | Varies     |

### Compliance Frameworks

- **OWASP LLM Top 10** — Prompt injection, sensitive data exposure, excessive agency
- **MITRE ATLAS** — Adversarial threat landscape for AI systems
- **NIST AI RMF** — AI risk management framework
- **ISO/IEC 42001** — AI management system standard
- **EU AI Act** — European AI regulation compliance
- **GDPR** — Data protection requirements
- **OWASP API Top 10** — API security best practices

### Attack Categories

| Category           | Examples                                |
| ------------------ | --------------------------------------- |
| Encoding           | Base64, ROT13, Leetspeak                |
| Social Engineering | Roleplay, trust building                |
| Injection          | Prompt injection, SQL injection         |
| Semantic           | Goal redirection, context poisoning     |
| Technical          | Gray-box probing, permission escalation |

### Risk Scoring (CVSS-based)

Each vulnerability receives a **0-10 risk score** based on:

- **Impact** — Severity if exploited
- **Exploitability** — Success rate likelihood
- **Human Factor** — Manual exploitation potential
- **Complexity** — Attack difficulty

### Reproducible Scans

```bash
# Use random seeds for reproducible results
uvx rogue-ai cli --random-seed 42
```

Perfect for regression testing and validating security fixes.

---

## Configuration

### Environment Variables

```bash
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-..."
GOOGLE_API_KEY="..."
```

### Config File (`.rogue/user_config.json`)

```json
{
  "evaluated_agent_url": "http://localhost:10001",
  "judge_llm": "openai/gpt-4o-mini"
}
```

---

## Key Features

| Feature                  | Description                                  |
| ------------------------ | -------------------------------------------- |
| 🔄 Dynamic Scenarios     | Auto-generate tests from business context    |
| 👀 Live Monitoring       | Watch agent conversations in real-time       |
| 📊 Comprehensive Reports | Markdown, CSV, JSON exports                  |
| 🔍 Multi-Faceted Testing | Policy compliance + security + resilience        |
| ⚡ Rogue Resilience      | Fault injection, cascade & recovery metrics    |
| 🤖 Model Support         | OpenAI, Anthropic, Google (via LiteLLM)      |
| 🛡️ CVSS Scoring          | Industry-standard risk assessment            |
| 🔁 Reproducible          | Deterministic scans with random seeds        |

---

## Documentation

- **[Quick Reference](./docs/QUICK_REFERENCE.md)** — One-page cheat sheet
- **[Red Team Workflow](./docs/RED_TEAM_WORKFLOW.md)** — Technical deep-dive
- **[Rogue Resilience](./docs/resilience/README.md)** — Chaos testing, dashboard, CLI
- **[Implementation Status](./docs/IMPLEMENTATION_STATUS.md)** — Feature breakdown
- **[Attack Mapping](./docs/ATTACK_VULNERABILITY_MAPPING.md)** — Vulnerability coverage

---

## Contributing

1. Fork the repository
2. Create a branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

Licensed under a proprietary license — see [LICENSE](LICENSE.md).

Free for personal and internal use. Commercial hosting requires licensing.
Contact: `hello@rogue.security`
