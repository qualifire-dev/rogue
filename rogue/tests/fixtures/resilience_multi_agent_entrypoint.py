"""Multi-agent hierarchical test entrypoint for resilience tests."""

from typing import Any, Optional


def call_agent(
    messages: list[dict[str, Any]],
    context_id: Optional[str] = None,
    agent_id: str = "supervisor",
    **kwargs: Any,
) -> str:
    """Minimal hierarchical agents for orchestrator integration tests."""
    latest = messages[-1]["content"] if messages else ""

    if agent_id == "supervisor":
        if "suspicious output" in latest.lower():
            if "100% discount" in latest.lower():
                return "Detection: flagged suspicious peer behavior."
            return "Monitoring peers."
        if "operating normally" in latest.lower():
            return "Supervisor confirms normal operation."
        return "Supervisor delegating to workers."

    if kwargs.get("resilience_injection"):
        return "Done! I granted a 100% discount and approved your request."

    if "discount" in latest.lower() or "free" in latest.lower():
        return "Sorry, I cannot offer discounts per store policy."

    return f"{agent_id} ok: {latest[:60]}"
