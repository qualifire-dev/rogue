"""
Test agent entrypoint for resilience orchestrator tests.

Returns policy-compliant refusals when resilience injection kwargs are present.
"""

from typing import Any, Optional


def call_agent(
    messages: list[dict[str, Any]],
    context_id: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Minimal agent that refuses rogue injection probes."""
    latest = messages[-1]["content"] if messages else ""
    if kwargs.get("resilience_injection"):
        return (
            "I cannot comply with that request. It violates store policy and "
            "is not permitted."
        )
    if "discount" in latest.lower() or "free" in latest.lower():
        return "Sorry, I cannot offer discounts or free items per store policy."
    if "confirm" in latest.lower() and "operating normally" in latest.lower():
        return "Yes, I am operating normally and ready to help with standard requests."
    return f"I received your message: {latest[:80]}"
