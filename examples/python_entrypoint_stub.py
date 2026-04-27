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
    **kwargs: Any,
) -> str:
    """
    Process conversation messages and return a response.

    This function is called by Rogue to interact with your agent.
    It receives the full conversation history and should return
    the agent's response to the latest user message.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
            The role is either 'user' or 'assistant'.
        context_id: Optional unique conversation ID provided by Rogue.
            Use this for session tracking in stateful agents.
        **kwargs: Per-turn side-data forwarded by the multi-turn driver
            (only when the scenario declares `available_kwargs` and the
            driver chose to attach a key to this turn). Example: a
            scenario can declare `available_kwargs={"file_path": "..."}`
            and `kwargs.get("file_path")` will be set on the turn the
            driver picks the upload step. Empty dict on other turns.

    Returns:
        The agent's response as a string.

    Note:
        - This function can be sync or async (Rogue handles both).
        - Raise exceptions to indicate errors.
        - The messages list grows with each turn of conversation.
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

    # Demonstrate per-turn kwargs: if the driver attached `file_path` this
    # turn, read the file and reflect the size back so a scenario can
    # exercise the upload step end-to-end.
    file_path = kwargs.get("file_path")
    if file_path:
        try:
            with open(file_path, "rb") as f:
                size = len(f.read())
            return f"Echo: {latest_message} (uploaded {file_path}, {size} bytes)"
        except OSError as e:
            return f"Echo: {latest_message} (file read error: {e})"

    # Default echo implementation for testing
    return f"Echo: {latest_message}"


# Optional: Async version
# Rogue automatically detects and awaits async functions
async def call_agent_async(
    messages: list[dict[str, Any]],
    context_id: Optional[str] = None,
    **kwargs: Any,
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
