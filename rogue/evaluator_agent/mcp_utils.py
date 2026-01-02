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


def create_mcp_client(
    url: str,
    transport: Transport,
    headers: Optional[dict[str, str]] = None,
) -> "Client[SSETransport | StreamableHttpTransport]":
    """
    Create an MCP client with the specified transport.

    The caller is responsible for entering and exiting the async context
    (via `async with client:` or manual `__aenter__`/`__aexit__` calls).

    Args:
        url: The URL of the MCP server to connect to.
        transport: The transport type to use (SSE or STREAMABLE_HTTP).
        headers: Optional HTTP headers to include in requests.

    Returns:
        An MCP client (not yet connected - caller must enter the async context).

    Raises:
        ValueError: If the transport type is not supported for MCP.
    """
    from fastmcp import Client
    from fastmcp.client import SSETransport, StreamableHttpTransport

    if transport == Transport.SSE:
        sse_transport: SSETransport = (
            SSETransport(url=url, headers=headers) if headers else SSETransport(url=url)
        )
        return Client[SSETransport](transport=sse_transport)
    elif transport == Transport.STREAMABLE_HTTP:
        http_transport: StreamableHttpTransport = (
            StreamableHttpTransport(url=url, headers=headers)
            if headers
            else StreamableHttpTransport(url=url)
        )
        return Client[StreamableHttpTransport](transport=http_transport)
    else:
        raise ValueError(f"Unsupported transport for MCP: {transport}")
