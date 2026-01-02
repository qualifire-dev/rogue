"""MCP Red Team Attacker Agent - Attacks using MCP protocol."""

from typing import TYPE_CHECKING, Dict, Optional

from loguru import logger

from ..mcp_utils import create_mcp_client
from .base_red_team_attacker_agent import BaseRedTeamAttackerAgent

if TYPE_CHECKING:
    from fastmcp import Client
    from fastmcp.client import SSETransport, StreamableHttpTransport


class MCPRedTeamAttackerAgent(BaseRedTeamAttackerAgent):
    """Red team attacker agent using MCP protocol."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._context_id_to_client: Dict[
            str,
            "Client[SSETransport | StreamableHttpTransport]",
        ] = {}

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Clean up MCP clients."""
        for client in self._context_id_to_client.values():
            await client.__aexit__(exc_type, exc_value, traceback)
        await super().__aexit__(exc_type, exc_value, traceback)

    async def _create_client(self) -> "Client[SSETransport | StreamableHttpTransport]":
        """Create a new MCP client."""
        if self._transport is None:
            raise ValueError("Transport is required for MCP")

        client = create_mcp_client(
            url=self._evaluated_agent_address,
            transport=self._transport,
        )
        await client.__aenter__()
        return client

    async def _get_or_create_client(
        self,
        context_id: str,
    ) -> "Client[SSETransport | StreamableHttpTransport]":
        """Get or create an MCP client for the given context."""
        if context_id not in self._context_id_to_client:
            self._context_id_to_client[context_id] = await self._create_client()
        return self._context_id_to_client[context_id]

    async def _send_message_to_evaluated_agent(
        self,
        message: str,
        session_id: Optional[str],
    ) -> str:
        """Send attack message via MCP protocol."""
        try:
            context_id = session_id or "default"
            client = await self._get_or_create_client(context_id)

            logger.debug(
                f"Sending MCP message to {self._evaluated_agent_address}",
                extra={"context_id": context_id, "message_preview": message[:100]},
            )

            tool_result = await client.call_tool(
                name="send_message",
                arguments={
                    "message": message,
                },
            )

            text_response = ""
            for part in tool_result.content:
                if part.type != "text":
                    logger.warning(
                        "Received non-text part in tool result",
                        extra={"type": part.type},
                    )
                    continue
                text_response += part.text

            return text_response or "No text response"

        except Exception as e:
            logger.error(
                f"Failed to send MCP message: {e}",
                extra={"agent_url": self._evaluated_agent_address},
            )
            return f"Error: {str(e)}"
