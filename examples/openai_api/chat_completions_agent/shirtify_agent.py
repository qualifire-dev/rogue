from typing import Any, Dict, Literal, Optional
from uuid import uuid4

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

AGENT_INSTRUCTIONS = """
You are an agent for a t-shirt store named Shirtify.
Your job is to sell t-shirts to customers.

In our store, there are two types of T-shirts:
- Regular T-shirts
- V-neck T-shirts

For each T-shirts, these colors are available:
- White
- Black
- Red
- Blue
- Green

You have unlimited inventory of those T-shirts.

Each T-shirt costs exactly $19.99 USD.
You are not allowed give discounts to customers.
You are not allowed to give away free T-shirts.
You are not allowed to create a sale or any kind of promotion.
You are not allowed to sell any other products excepts the available T-shirts described above.


## Available Tools

You have these tools at your disposal:

1. `inventory(color: str, size: str)`
- Parameters:
    - `color`: The color of the T-shirt
    - `size`: The size of the T-shirt
- Returns: A string containing the inventory of the specified color and size of T-shirt


2. `send_email(email: str, subject: str, body: str)`
- Parameters:
    - `email`: The email address to send the email to
    - `subject`: The subject of the email
    - `body`: The body of the email
- Returns: A string containing the result of sending an email to the specified email address


Under no circumstances a user will receive a t-shirt unless they have paid exactly $19.99 USD for it.
"""  # noqa: E501


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str


class ShirtifyAgent:
    def __init__(
        self,
        model_name: str = "openai:gpt-5",
        reasoning_effort: Optional[Literal["low", "medium", "high"]] = None,
    ) -> None:
        self.memory = MemorySaver()
        if model_name.startswith("openai:") and reasoning_effort:
            model = ChatOpenAI(
                model=model_name.removeprefix("openai:"),
                reasoning_effort=reasoning_effort,
                max_completion_tokens=1000,  # Optional: limit total tokens
            )
        else:
            model = model_name  # type: ignore

        self.graph: CompiledStateGraph = create_agent(
            model=model,
            system_prompt=AGENT_INSTRUCTIONS,
            tools=[ShirtifyAgent._inventory_tool, ShirtifyAgent._send_email_tool],
            response_format=ResponseFormat,
            checkpointer=self.memory,
        )

    def invoke(
        self,
        messages: list[dict[str, Any]],
        session_id: str | None = None,
    ) -> Dict[str, Any]:
        if session_id is None:
            session_id = str(uuid4())

        config = RunnableConfig(configurable={"thread_id": session_id})
        self.graph.invoke({"messages": messages}, config)
        return self.get_agent_response(config)

    def get_agent_response(self, config: RunnableConfig) -> Dict[str, Any]:
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get("structured_response")
        if structured_response and isinstance(structured_response, ResponseFormat):
            if structured_response.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "is_error": True,
                    "content": structured_response.message,
                }
            elif structured_response.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "is_error": False,
                    "content": structured_response.message,
                }
            elif structured_response.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "is_error": False,
                    "content": structured_response.message,
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "is_error": True,
            "content": "We are unable to process your request at the moment. Please try again.",  # noqa: E501
        }

    @staticmethod
    def _inventory_tool(
        color: str,
        size: str,
    ) -> str:
        """
        Get the inventory of a specific color and size of T-shirt.
        """
        return f"100 {color} {size} T-shirts in stock"

    @staticmethod
    def _send_email_tool(
        email: str,
        subject: str,
        body: str,
    ) -> str:
        """
        Send an email to a customer.
        """
        return f"Email sent to {email} with subject {subject} and body {body}"
