"""
This is a MCP wrapper for the Shirtify Agent.
Its only purpose is to allow communication with the agent via MCP.

The agent itself can be implemented using any agent framework,
you only need to implement the send_message tool.
"""

from loguru import logger
from mcp.server.fastmcp import Context, FastMCP
from starlette.requests import Request

from .shirtify_agent import ShirtifyAgent

agent = ShirtifyAgent()
mcp = FastMCP(
    "shirtify_agent_mcp",
    port=10001,
    host="127.0.0.1",
)


@mcp.tool()
def send_message(message: str, context: Context) -> str:
    session_id: str | None = None
    try:
        request: Request = context.request_context.request  # type: ignore

        # The session id should be in the headers for streamable-http transport
        session_id = request.headers.get("mcp-session-id")

        # The session id might also be in query param when using sse transport
        if session_id is None:
            session_id = request.query_params.get("session_id")
    except Exception:
        session_id = None
        logger.exception("Error while extracting session id")

    if session_id is None:
        logger.error("Couldn't extract session id")

    # Invoking our agent
    response = agent.invoke(message, session_id)
    return response.get("content", "")
