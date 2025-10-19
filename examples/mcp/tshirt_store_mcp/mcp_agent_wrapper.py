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

agent = ShirtifyAgent()
mcp = FastMCP("shirtify_agent_mcp")


@mcp.tool()
def send_message(message: str, context: Context) -> Dict[str, Any]:
    # Invoking our agent
    raw_tool_result = agent.invoke(message, context.client_id)

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
