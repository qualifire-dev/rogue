"""
Python entrypoint for Rogue agent evaluation - Shirtify T-shirt Store Agent.

This file connects the Shirtify LangGraph agent to Rogue's Python entrypoint
protocol for evaluation and red teaming.

Usage:
    rogue --protocol=python \
        --python-entrypoint-file=examples/tshirt_store_langgraph_agent/python_entrypoint_shirtify.py
"""

from typing import Any, Optional

from shirtify_langgraph_agent import ShirtifyAgent

# Initialize the agent once at module load
agent = ShirtifyAgent()


def call_agent(
    messages: list[dict[str, Any]],
    context_id: Optional[str] = None,
) -> str:
    """
    Process conversation messages and return a response from the Shirtify agent.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
            Example:
                [
                    {"role": "user", "content": "Show me blue t-shirts"},
                    {"role": "assistant", "content": "Here are some options..."},
                    {"role": "user", "content": "I'll take the first one"}
                ]
        context_id: Optional unique conversation ID provided by Rogue.
            Use this as the session ID for stateful agents.

    Returns:
        The agent's response as a string.
    """
    if not messages:
        return "Hello! I'm the Shirtify assistant. \
        How can I help you find the perfect t-shirt today?"

    # Use context_id from Rogue as session ID (or generate one for local testing)
    session_id = context_id or "local-test-session"

    # Get the latest user message
    latest_message = messages[-1]["content"]

    # Invoke the agent
    response = agent.invoke(latest_message, session_id)

    return response.get("content", "I'm sorry, I couldn't process that request.")


# For local testing
if __name__ == "__main__":
    test_messages = [
        {"role": "user", "content": "What t-shirts do you have?"},
    ]

    print("Testing Shirtify agent:")
    print(f"  Input: {test_messages[-1]['content']}")
    print(f"  Output: {call_agent(test_messages)}")
