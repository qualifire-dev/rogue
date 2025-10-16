# Rogue - The AI Agent Evaluator

![](https://pixel.qualifire.ai/api/record/rogue)

<div align="center">

[![License: ELASTIC](https://img.shields.io/badge/License-elastic-yellow.svg)](https://www.elastic.co/licensing/elastic-license)
![Tests](https://github.com/qualifire-dev/rogue/actions/workflows/test.yml/badge.svg?branch=main)

<img src="./freddy-rogue.png" width="200"/>

</div>

Rogue is a powerful tool designed to evaluate the performance, compliance, and reliability of AI agents. It pits a dynamic `EvaluatorAgent` against your agent using Google's A2A protocol, testing it with a range of scenarios to ensure it behaves exactly as intended.

## Architecture

Rogue operates on a **client-server architecture**:

- **Rogue Server**: Contains the core evaluation logic
- **Client Interfaces**: Multiple interfaces that connect to the server:
  - **TUI (Terminal UI)**: Modern terminal interface built with Go and Bubble Tea
  - **Web UI**: Gradio-based web interface
  - **CLI**: Command-line interface for automated evaluation and CI/CD

This architecture allows for flexible deployment and usage patterns, where the server can run independently and multiple clients can connect to it simultaneously.

https://github.com/user-attachments/assets/b5c04772-6916-4aab-825b-6a7476d77787

## 🔥 Quick Start

### Prerequisites

- `uvx` - If not installed, follow [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.10+
- An API key for an LLM provider (e.g., OpenAI, Google, Anthropic).

### Installation

#### Option 1: Quick Install (Recommended)

Use our automated install script to get up and running quickly:

```bash
# TUI
uvx rogue-ai

# Web UI
uvx rogue-ai ui

# CLI / CI/CD
uvx rogue-ai cli
```

#### Option 2: Manual Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/qualifire-dev/rogue.git
    cd rogue
    ```

2.  **Install dependencies:**

    If you are using uv:

    ```bash
    uv sync
    ```

    Or, if you are using pip:

    ```bash
    pip install -e .
    ```

3.  **OPTIONALLY: Set up your environment variables:**
    Create a `.env` file in the root directory and add your API keys. Rogue uses `LiteLLM`, so you can set keys for various providers.
    ```env
    OPENAI_API_KEY="sk-..."
    ANTHROPIC_API_KEY="sk-..."
    GOOGLE_API_KEY="..."
    ```

### Running Rogue

Rogue operates on a client-server architecture where the core evaluation logic runs in a backend server, and various clients connect to it for different interfaces.

#### Default Behavior

When you run `uvx rogue-ai` without any mode specified, it:

1. Starts the Rogue server in the background
2. Launches the TUI (Terminal User Interface) client

```bash
uvx rogue-ai
```

#### Available Modes

- **Default (Server + TUI)**: `uvx rogue-ai` - Starts server in background + TUI client
- **Server**: `uvx rogue-ai server` - Runs only the backend server
- **TUI**: `uvx rogue-ai tui` - Runs only the TUI client (requires server running)
- **Web UI**: `uvx rogue-ai ui` - Runs only the Gradio web interface client (requires server running)
- **CLI**: `uvx rogue-ai cli` - Runs non-interactive command-line evaluation (requires server running, ideal for CI/CD)

#### Mode Arguments

##### Server Mode

```bash
uvx rogue-ai server [OPTIONS]
```

**Options:**

- `--host HOST` - Host to run the server on (default: 127.0.0.1 or HOST env var)
- `--port PORT` - Port to run the server on (default: 8000 or PORT env var)
- `--debug` - Enable debug logging

##### TUI Mode

```bash
uvx rogue-ai tui [OPTIONS]
```

##### Web UI Mode

```bash
uvx rogue-ai ui [OPTIONS]
```

**Options:**

- `--rogue-server-url URL` - Rogue server URL (default: http://localhost:8000)
- `--port PORT` - Port to run the UI on
- `--workdir WORKDIR` - Working directory (default: ./.rogue)
- `--debug` - Enable debug logging

##### CLI Mode

```bash
uvx rogue-ai cli [OPTIONS]
```

**Options:**

- `--config-file FILE` - Path to config file
- `--rogue-server-url URL` - Rogue server URL (default: http://localhost:8000)
- `--evaluated-agent-url URL` - URL of the agent to evaluate
- `--evaluated-agent-auth-type TYPE` - Auth method (no_auth, api_key, bearer_token, basic)
- `--evaluated-agent-credentials CREDS` - Credentials for the agent
- `--input-scenarios-file FILE` - Path to scenarios file (default: <workdir>/scenarios.json)
- `--output-report-file FILE` - Path to output report file
- `--judge-llm MODEL` - Model for evaluation and report generation
- `--judge-llm-api-key KEY` - API key for LLM provider
- `--business-context TEXT` - Business context description
- `--business-context-file FILE` - Path to business context file
- `--deep-test-mode` - Enable deep test mode
- `--workdir WORKDIR` - Working directory (default: ./.rogue)
- `--debug` - Enable debug logging

#### Web UI Mode

To launch the Gradio web UI specifically:

```bash
uvx rogue-ai ui
```

Navigate to the URL displayed in your terminal (usually `http://127.0.0.1:7860`) to begin.

---

## Example: Testing the T-Shirt Store Agent

This repository includes a simple example agent that sells T-shirts. You can use it to see Rogue in action.

### Option 1: All-in-One (Recommended)

The easiest way to try Rogue with the example agent is to use the `--example` flag, which starts both Rogue and the example agent automatically:

```bash
uvx rogue-ai --example=tshirt_store
```

This will:

- Start the T-Shirt Store agent on `http://localhost:10001`
- Launch Rogue with the TUI interface
- Automatically clean up when you exit

You can customize the host and port:

```bash
uvx rogue-ai --example=tshirt_store --example-host localhost --example-port 10001
```

### Option 2: Manual Setup

If you prefer to run the example agent separately:

1. **Install example dependencies:**

   If you are using uv:

   ```bash
   uv sync --group examples
   ```

   or, if you are using pip:

   ```bash
   pip install -e .[examples]
   ```

2. **Start the example agent server** in a separate terminal:

   If you are using uv:

   ```bash
   uv run python -m examples.tshirt_store_agent
   ```

   Or using the script command:

   ```bash
   uv run rogue-ai-example-tshirt
   ```

   Or if installed:

   ```bash
   uvx rogue-ai-example-tshirt
   ```

   This will start the agent on `http://localhost:10001`.

3. **Configure Rogue** in the UI to point to the example agent:

   - **Agent URL**: `http://localhost:10001`
   - **Authentication**: `no-auth`

4. **Run the evaluation** and watch Rogue test the T-Shirt agent's policies!

   You can use either the TUI (`uvx rogue-ai`) or Web UI (`uvx rogue-ai ui`) mode.

---

## 🔧 CLI Mode

The CLI mode provides a **non-interactive** command-line interface for evaluating AI agents against predefined scenarios. It connects to the Rogue server to perform evaluations and is **ideal for CI/CD pipelines** and automated testing workflows.

### 🚀 Usage

The CLI mode requires the Rogue server to be running. You can either:

1. **Start server separately:**

   ```bash
   # Terminal 1: Start the server
   uvx rogue-ai server

   # Terminal 2: Run CLI evaluation
   uvx rogue-ai cli [OPTIONS]
   ```

2. **Use the default mode (starts server + TUI, then use TUI for evaluation)**

For development or if you prefer to install locally:

```bash
git clone https://github.com/qualifire-dev/rogue.git
cd rogue
uv sync
uv run -m rogue cli [OPTIONS]
```

Or, if you are using pip:

```bash
git clone https://github.com/qualifire-dev/rogue.git
cd rogue
pip install -e .
uv run -m rogue cli [OPTIONS]
```

---

### 📓 CLI Arguments

> **Note**: CLI mode is **non-interactive** and designed for automated evaluation workflows, making it perfect for CI/CD pipelines.

| Argument                      | Required                                               | Default Value                   | Description                                                                                                                                             |
| ----------------------------- | ------------------------------------------------------ | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| --workdir                     | No                                                     | `./.rogue`                      | Directory to store outputs and defaults.                                                                                                                |
| --config-file                 | No                                                     | `<workdir>/user_config.json`    | Path to a config file generated by the UI. Values from this file are used unless overridden via CLI. If the file does not exist, only cli will be used. |
| --rogue-server-url            | No                                                     | `http://localhost:8000`         | URL of the Rogue server to connect to.                                                                                                                  |
| --evaluated-agent-url         | Yes                                                    |                                 | The URL of the agent to evaluate.                                                                                                                       |
| --evaluated-agent-auth-type   | No                                                     | `no_auth`                       | Auth method. Can be one of: `no_auth`, `api_key`, `bearer_token`, `basic`.                                                                              |
| --evaluated-agent-credentials | Yes\*<br/>if `auth_type` is not `no_auth`              |                                 | Credentials for the agent (if required).                                                                                                                |
| --input-scenarios-file        | Yes                                                    | `<workdir>/scenarios.json`      | Path to scenarios file.                                                                                                                                 |
| --output-report-file          | No                                                     | `<workdir>/report.md`           | Where to save the markdown report.                                                                                                                      |
| --judge-llm                   | Yes                                                    |                                 | Model name for LLM evaluation (Litellm format).                                                                                                         |
| --judge-llm-api-key           | No                                                     |                                 | API key for LLM (see environment section).                                                                                                              |
| --business-context            | Yes\*<br/>Unless `--business-context-file` is supplied |                                 | Business context as a string.                                                                                                                           |
| --business-context-file       | Yes\*<br/>Unless `--business-context` is supplied      | `<workdir>/business_context.md` | OR path to file containing the business context.<br/>If both given, `--business-context` has priority                                                   |
| --deep-test-mode              | No                                                     | `False`                         | Enables extended testing behavior.                                                                                                                      |
| --debug                       | No                                                     | `False`                         | Enable verbose logging.                                                                                                                                 |

### 📊 Config file

The config file is automatically generated when running the UI. \
We will check for a config file in `<workdir>/user_config.json` and use it if it exists. \
The config file is a JSON object that can contain all or a subset of the fields from the CLI arguments, except for `--config-file`. \
Other keys in the config file are ignored. \
Just remember to use snake_case keys. (e.g. `--evaluated-agent-url` becomes `evaluated_agent_url`).

### Notes

1. ⚠️ Either `--business-context` or `--business-context-file` must be provided.
2. ⚠️ Fields marked as Required are required unless supplied via the config file.

---

### Examples

### With only a config file:

with our business context located at `./.rogue/business_context.md`

#### `./.rogue/user_config.json`

```json
{
  "evaluated_agent_url": "http://localhost:10001",
  "judge_llm": "openai/o4-mini"
}
```

#### Execution

```bash
uvx rogue-ai cli
```

### Same example without a config file:

#### Execution

```bash
uvx rogue-ai cli \
    --evaluated-agent-url http://localhost:10001 \
    --judge-llm openai/o4-mini \
    --business-context-file './.rogue/business_context.md'
```

---

## Key Features

- **🔄 Dynamic Scenario Generation**: Automatically creates a comprehensive test suite from your high-level business context.
- **👀 Live Evaluation Monitoring**: Watch the interaction between the Evaluator and your agent in a real-time chat interface.
- **📊 Comprehensive Reporting**: Generates a detailed summary of the evaluation, including pass/fail rates, key findings, and recommendations.
- **🔍 Multi-Faceted Testing**: Natively supports testing for policy compliance, with a flexible framework to expand to other areas like prompt injection or safety.
- **🤖 Broad Model Support**: Compatible with a wide range of models from providers like OpenAI, Google (Gemini), and Anthropic.
- **🎯 User-Friendly Interface**: A simple, step-by-step Gradio UI guides you through configuration, execution, and reporting.

---

## How It Works

Rogue's workflow is designed to be simple and intuitive, managed entirely through its web interface.

1.  **Configure**: You provide the endpoint and authentication details for the agent you want to test, and select the LLMs you want Rogue to use for its services (scenario generation, judging).
2.  **Generate Scenarios**: You input the "business context" or a high-level description of what your agent is supposed to do. Rogue's `LLM Service` uses this context to generate a list of relevant test scenarios. You can review and edit these scenarios.
3.  **Run & Evaluate**: You start the evaluation. The `Scenario Evaluation Service` spins up the `EvaluatorAgent`, which begins a conversation with your agent for each scenario. You can watch this conversation happen live.
4.  **View Report**: Once all scenarios are complete, the `LLM Service` analyzes the results and generates a Markdown-formatted report, giving you a clear summary of your agent's performance.

---

## Contributing

Contributions are welcome! If you'd like to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes and commit them (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature-name`).
5.  Open a pull request.

Please make sure to update tests as appropriate.

## License

This project is licensed under the ELASTIC License - see the [LICENSE](LICENSE) file for details.
