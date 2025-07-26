# Rogue Agent CI/CD

You can use Rogue as part of your CI/CD pipeline to test your AI agent's functionality. \
In this example, we use a GitHub Actions, but this should be easily adaptable to other CI/CD platforms.


---

## Workflow Overview

Our workflow consists of the following steps:

Preparations:
1.  **Checks out the repository.**
2.  **Installs `uv` and python.** you can choose to use python as-is without uv if you prefer.
3.  **Installs Rogue.**

Execution: 
1.  **Starts the AI agent** in the background.
2.  **Waits for the agent to become ready** by repeatedly checking the agent-card URL.
3.  **Executes Rogue** to run tests against the locally started agent.

---


## Notes:
1. Rogue can take a long time to run. Consider setting a timeout to avoid unexpected costs.
2. Don't forget to set the llm provider api key (OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY / gcloud login / etc) in your CI/CD environment.
3. Make sure to adjust the readiness check URL to match your agent's URL.
4. Make sure to go over the Rogue CLI documentation to help you configure Rogue CLI to match your needs.

---

## `.github/workflows/rogue.yml`

```yaml
name: Rogue

on:
  pull_request:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  run-rogue:
    runs-on: ubuntu-latest
    
    # Notice! Rogue can take a long time to run. consider setting a timeout to avoid unexpected costs.
    timeout-minutes: 60
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version-file: ".python-version"

      - name: Install rogue
        run: uv pip install -e . --system

      - name: Run rogue
        shell: bash
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          echo "🚀 Starting AI agent..."
          # Command to start your specific AI agent
          # ----> Notice! Replace with your own agent start command <----
          uv run examples/tshirt_store_agent --host 127.0.0.1 --port 10001 &
          
          AGENT_PID=$!
          echo "Agent started with PID: $AGENT_PID"
          # This trap ensures the agent process is killed when the script exits, even if an error occurs.
          trap 'echo "🛑 Stopping agent..."; kill $AGENT_PID' EXIT
          
          echo "⏳ Waiting for agent to be ready..."
          # ----> Update this URL if needed. <----
          curl --retry 10 --retry-delay 5 --retry-connrefused -s --fail -o /dev/null \
            http://localhost:10001/.well-known/agent.json
          
          echo "🚀 Running rogue..."
          # Rogue CLI command.
          # ----> Adjust the cli arguments based on your needs. See the CLI documentation for more details. <----
          uv run -m rogue cli \
            --evaluated-agent-url http://localhost:10001 \
            --judge-llm-model openai/o4-mini \
            --workdir './examples/tshirt_store_agent/.rogue'
```
