"""
Shared utilities for MCP client creation.

This module provides common functionality for creating MCP clients
with different transport types (SSE or Streamable HTTP).
"""

from typing import TYPE_CHECKING, Optional

from rogue_sdk.types import Transport

if TYPE_CHECKING:
    from fastmcp import Client
    from fastmcp.client import SSETransport, StreamableHttpTransport


async def create_mcp_client(
    url: str,
    transport: Transport,
    headers: Optional[dict[str, str]] = None,
) -> "Client[SSETransport | StreamableHttpTransport]":
    """
    Create and initialize an MCP client with the specified transport.

    Args:
        url: The URL of the MCP server to connect to.
        transport: The transport type to use (SSE or STREAMABLE_HTTP).
        headers: Optional HTTP headers to include in requests.

    Returns:
        An initialized MCP client ready for use.

    Raises:
        ValueError: If the transport type is not supported for MCP.
    """
    from fastmcp import Client
    from fastmcp.client import SSETransport, StreamableHttpTransport

    client: Client[SSETransport | StreamableHttpTransport] | None = None

    if transport == Transport.SSE:
        transport_instance = (
            SSETransport(url=url, headers=headers) if headers else SSETransport(url=url)
        )
        client = Client[SSETransport](transport=transport_instance)
    elif transport == Transport.STREAMABLE_HTTP:
        transport_instance = (
            StreamableHttpTransport(url=url, headers=headers)
            if headers
            else StreamableHttpTransport(url=url)
        )
        client = Client[StreamableHttpTransport](transport=transport_instance)
    else:
        raise ValueError(f"Unsupported transport for MCP: {transport}")

    if not client:
        raise ValueError(f"Failed to create client for transport: {transport}")

    await client.__aenter__()
    return client
