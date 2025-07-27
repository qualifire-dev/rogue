from typing import Dict, Any, AsyncIterable, Literal

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent
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

Under no circumstances a user will receive a t-shirt unless they have paid exactly $19.99 USD for it.
"""  # noqa: E501


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str


class ShirtifyAgent:
    def __init__(self, model: str = "openai:gpt-4o") -> None:
        self.memory = MemorySaver()

        self.graph: CompiledStateGraph = create_react_agent(
            model=model,
            prompt=AGENT_INSTRUCTIONS,
            tools=[],
            response_format=ResponseFormat,
            checkpointer=self.memory,
        )

    def invoke(self, query: str, session_id: str) -> Dict[str, Any]:
        config = RunnableConfig(configurable={"thread_id": session_id})
        self.graph.invoke({"messages": [("user", query)]}, config)
        return self.get_agent_response(config)

    async def stream(
        self,
        query: str,
        session_id: str,
    ) -> AsyncIterable[Dict[str, Any]]:
        inputs = {"messages": [("user", query)]}
        config = RunnableConfig(configurable={"thread_id": session_id})

        for item in self.graph.stream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": message.content,
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": message.content,
                }

        yield self.get_agent_response(config)

    def get_agent_response(self, config: RunnableConfig) -> Dict[str, Any]:
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get("structured_response")
        if structured_response and isinstance(structured_response, ResponseFormat):
            if structured_response.status in ("input_required", "error"):
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message,
                }
            elif structured_response.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured_response.message,
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "We are unable to process your request at the moment. Please try again.",  # noqa: E501
        }


global root_agent
root_agent = ShirtifyAgent()
