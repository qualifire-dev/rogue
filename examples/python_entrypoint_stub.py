"""
Example Python entrypoint for Rogue agent evaluation.

This file demonstrates how to create a Python entrypoint for testing
agents without A2A or MCP protocols. Rogue will dynamically import
this file and call the `call_agent` function.


Or via TUI:
    1. Select "Python" as the protocol
    2. Enter the path to your Python file

The call_agent function receives the full conversation history and
should return the agent's response as a string.
"""

from typing import Any, Optional


def call_agent(
    messages: list[dict[str, Any]],
    context_id: Optional[str] = None,
) -> str:
    """
    Process conversation messages and return a response.

    This function is called by Rogue to interact with your agent.
    It receives the full conversation history and should return
    the agent's response to the latest user message.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
            The role is either 'user' or 'assistant'.
            Example:
                [
                    {"role": "user", "content": "Hello, how are you?"},
                    {"role": "assistant", "content": "I'm doing well, thanks!"},
                    {"role": "user", "content": "What can you help me with?"}
                ]
        context_id: Optional unique conversation ID provided by Rogue.
            Use this for session tracking in stateful agents.
            Each conversation gets a unique context_id that persists
            across all messages in that conversation.

    Returns:
        The agent's response as a string.

    Note:
        - This function can be sync or async (Rogue handles both)
        - Raise exceptions to indicate errors (Rogue will catch and log them)
        - The messages list grows with each turn of conversation
        - context_id is optional for backward compatibility
    """
    # Extract the latest user message
    latest_message = messages[-1]["content"] if messages else ""

    # ==============================================
    # Replace this with your actual agent logic!
    # ==============================================
    #
    # Example integrations:
    #
    # 1. OpenAI API:
    #     from openai import OpenAI
    #     client = OpenAI()
    #     response = client.chat.completions.create(
    #         model="gpt-4",
    #         messages=messages
    #     )
    #     return response.choices[0].message.content
    #
    # 2. LangChain:
    #     from langchain_openai import ChatOpenAI
    #     from langchain_core.messages import HumanMessage, AIMessage
    #     chat = ChatOpenAI()
    #     lc_messages = [
    #         HumanMessage(content=m["content"]) if m["role"] == "user"
    #         else AIMessage(content=m["content"])
    #         for m in messages
    #     ]
    #     response = chat.invoke(lc_messages)
    #     return response.content
    #
    # 3. Local model with transformers:
    #     from transformers import pipeline
    #     pipe = pipeline("text-generation", model="...")
    #     prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    #     return pipe(prompt)[0]["generated_text"]

    # Default echo implementation for testing
    return f"Echo: {latest_message}"


# Optional: Async version
# Rogue automatically detects and awaits async functions
async def call_agent_async(
    messages: list[dict[str, Any]],
    context_id: Optional[str] = None,
) -> str:
    """
    Async version of call_agent.

    If you rename this to `call_agent`, Rogue will use it instead.
    Useful for agents that make async API calls.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
        context_id: Optional unique conversation ID for session tracking.
    """
    import asyncio

    # Simulate async processing
    await asyncio.sleep(0.1)

    latest_message = messages[-1]["content"] if messages else ""
    # context_id can be used for session management
    return f"Async Echo (session: {context_id}): {latest_message}"
