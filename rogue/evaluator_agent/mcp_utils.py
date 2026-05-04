"""
Shared utilities for MCP client creation.

This module provides common functionality for creating MCP clients
with different transport types (SSE or Streamable HTTP).
"""

from typing import TYPE_CHECKING, Optional
from urllib.parse import urlparse, urlunparse

from rogue_sdk.types import Transport

if TYPE_CHECKING:
    from fastmcp import Client
    from fastmcp.client import SSETransport, StreamableHttpTransport


# FastMCP's default mount paths for the two supported transports — these
# come from ``fastmcp.settings`` (``streamable_http_path = "/mcp"``,
# ``sse_path = "/sse"``). Users routinely paste the bare server URL
# (``http://localhost:10002``), so we append the default path on their
# behalf when no explicit path is provided. Anyone running a non-FastMCP
# server with a custom mount can override by pasting the full path.
_DEFAULT_TRANSPORT_PATHS: dict[Transport, str] = {
    Transport.STREAMABLE_HTTP: "/mcp",
    Transport.SSE: "/sse",
}


def _normalize_mcp_url(url: str, transport: Transport) -> str:
    """Append the FastMCP default mount path when the URL has none.

    Preserves any user-supplied path (``/api/mcp``, ``/sse``, etc.) so the
    auto-append only kicks in for the common ``http://host:port`` /
    ``http://host:port/`` case where the connect would otherwise hit the
    wrong endpoint and the server would reply with ``Session terminated``.
    """
    parsed = urlparse(url)
    if parsed.path and parsed.path != "/":
        return url
    default_path = _DEFAULT_TRANSPORT_PATHS.get(transport)
    if not default_path:
        return url
    return urlunparse(parsed._replace(path=default_path))


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

    url = _normalize_mcp_url(url, transport)

    # Construct as the union-typed Client so the return type matches the
    # signature; without the explicit generic parameter, ty infers the
    # concrete `Client[SSETransport]` / `Client[StreamableHttpTransport]`
    # which doesn't unify with the declared union return.
    if transport == Transport.SSE:
        sse_transport: SSETransport = (
            SSETransport(url=url, headers=headers) if headers else SSETransport(url=url)
        )
        return Client[SSETransport | StreamableHttpTransport](transport=sse_transport)
    elif transport == Transport.STREAMABLE_HTTP:
        http_transport: StreamableHttpTransport = (
            StreamableHttpTransport(url=url, headers=headers)
            if headers
            else StreamableHttpTransport(url=url)
        )
        return Client[SSETransport | StreamableHttpTransport](transport=http_transport)
    else:
        raise ValueError(f"Unsupported transport for MCP: {transport}")
