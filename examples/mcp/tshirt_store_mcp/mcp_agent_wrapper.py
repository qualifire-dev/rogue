"""
This is a MCP wrapper for the Shirtify Agent.
Its only purpose is to allow communication with the agent via MCP.

The agent itself can be implemented using any agent framework,
you only need to implement the send_message tool.
"""

from typing import Any, Dict

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import CallToolResult, TextContent
from shirtify_agent import ShirtifyAgent
from starlette.requests import Request

agent = ShirtifyAgent()
mcp = FastMCP(
    "shirtify_agent_mcp",
    port=10001,
    host="127.0.0.1",
)


@mcp.tool()
def send_message(message: str, context: Context) -> Dict[str, Any]:
    session_id: str | None = None
    try:
        request: Request = context.request_context.request  # type: ignore
        session_id = request.query_params.get("session_id")
    except Exception:
        print("No session ID found in request")
        session_id = None

    # Invoking our agent
    raw_tool_result = agent.invoke(message, session_id)

    # Preparing the response
    return CallToolResult(
        content=[
            TextContent(
                text=raw_tool_result.get("content", ""),
                type="text",
            ),
        ],
        isError=raw_tool_result.get("is_error", False),
    ).model_dump()
