# Rogue — AI Agent Evaluator & Red Team Platform

![](https://pixel.qualifire.ai/api/record/rogue)

<div align="center">

<a href="https://trendshift.io/repositories/15191" target="_blank"><img src="https://trendshift.io/api/badge/repositories/15191" alt="qualifire-dev%2Frogue | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

![Tests](https://github.com/qualifire-dev/rogue/actions/workflows/test.yml/badge.svg?branch=main)

<img src="./freddy-rogue.png" width="200"/>

**Stress-test your AI agents before attackers do.**

[Discord Community](https://discord.gg/EUfAt7ZDeK) · [Quick Start](#-quick-start) · [Documentation](./docs/)

</div>

---

## Two Ways to Harden Your Agent

<table>
<tr>
<td width="50%" valign="top">

### 🎯 Automatic Evaluation

Test your agent against **business policies** and expected behaviors.

- Define scenarios & expected outcomes
- Verify compliance with business rules
- Watch live conversations as Rogue probes your agent
- Get detailed pass/fail reports with reasoning
- **Scenario Editor**: Create custom test scenarios (e.g., user requests discount → agent should refuse)

**Best for:** Regression testing, behavior validation, policy compliance

</td>
<td width="50%" valign="top">

### 🔴 Red Teaming

Simulate **adversarial attacks** to find security vulnerabilities.

- 75+ vulnerabilities across 12 security categories
- 20 attack techniques (encoding, social engineering, injection)
- CVSS-based risk scoring
- 8 compliance frameworks (OWASP, MITRE, NIST, GDPR, EU AI Act)

**Best for:** Security audits, penetration testing, compliance reporting

</td>
</tr>
</table>

---

## Architecture

Rogue operates on a **client-server architecture** with multiple interfaces:

| Component  | Description                                 |
| ---------- | ------------------------------------------- |
| **Server** | Core evaluation & red team logic            |
| **TUI**    | Modern terminal interface (Go + Bubble Tea) |
| **CLI**    | Non-interactive mode for CI/CD pipelines    |

![Rogue Scenario Editor Demo](./rogue-scenario-editor-demo.mov)

*Example: Scenario Editor showing a user requesting a discount. The agent correctly refuses to provide discounts, demonstrating policy compliance testing.*

### Supported Protocols

| Protocol | Transport | Description |
|----------|-----------|-------------|
| **A2A** | HTTP | [Google's Agent-to-Agent](https://a2a-protocol.org/latest/) protocol |
| **MCP** | SSE, STREAMABLE_HTTP | [Model Context Protocol](https://modelcontextprotocol.io/) via `send_message` tool |
| **Python** | — | Direct Python function calls (no network protocol) |

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

### Apple Silicon (M1/M2/M3) Setup

On Apple Silicon Macs, you may need to install Python 3.10+ using `uv`, as the system Python may be older:

```bash
# Install uv (provides uvx)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (add to ~/.zshrc for persistence)
export PATH="$HOME/.local/bin:$PATH"

# Install Python 3.11+ using uv (required for Rogue)
uv python install 3.11

# Verify Python version
uv python list

# Clone the repository
git clone https://github.com/qualifire-dev/rogue.git
cd rogue

# Update configuration for A2A protocol (if using example agent)
# Edit .rogue/user_config.json and set:
#   "protocol": "a2a"
#   "evaluated_agent_url": "http://localhost:10001"

# Start the server with example agent
uvx rogue-ai server --example=tshirt_store --host 127.0.0.1 --port 8000

# In a new terminal, launch the TUI
export PATH="$HOME/.local/bin:$PATH"
uvx rogue-ai tui
```

**Note:** The TUI requires an interactive terminal. On macOS, you may need to run it in a new Terminal window. If you encounter "device not configured" errors, ensure you're running the TUI in an interactive terminal session.

### Try It With the Example Agent

```bash
# All-in-one: starts both Rogue and a sample T-shirt store agent
uvx rogue-ai --example=tshirt_store
```

Configure in the UI:

- **Agent URL**: `http://localhost:10001`
- **Protocol**: `A2A` (for the example agent)
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
| `--deep-test-mode`       | Extended testing                            |

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
| 🔍 Multi-Faceted Testing | Policy compliance + security vulnerabilities |
| 🤖 Model Support         | OpenAI, Anthropic, Google (via LiteLLM)      |
| 🛡️ CVSS Scoring          | Industry-standard risk assessment            |
| 🔁 Reproducible          | Deterministic scans with random seeds        |

---

## Documentation

- **[Quick Reference](./docs/QUICK_REFERENCE.md)** — One-page cheat sheet
- **[Red Team Workflow](./docs/RED_TEAM_WORKFLOW.md)** — Technical deep-dive
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
Contact: `admin@qualifire.ai`
