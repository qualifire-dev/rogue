# LangGraph checkpoint recovery example

Demonstrates optional LangGraph checkpoint snapshot/restore during resilience
experiments. Requires LangGraph (`uv sync --group examples`).

## Run

```bash
uv sync --group examples
uv run python -m examples.resilience_langgraph_recovery.run_recovery_demo
```

The demo uses a deterministic LangGraph (no LLM API key required).
