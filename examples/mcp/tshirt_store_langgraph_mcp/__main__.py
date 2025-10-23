from typing import Literal

import click
from dotenv import load_dotenv

from .mcp_agent_wrapper import get_mcp_server

load_dotenv()


@click.command()
@click.option("--host", "host", default="127.0.0.1", help="Host to run the server on")
@click.option("--port", "port", default=10001, help="Port to run the server on")
@click.option(
    "--transport",
    "transport",
    default="streamable-http",
    choices=["streamable-http", "sse"],
    help="Transport to use for the mcp server",
)
def main(host: str, port: int, transport: Literal["streamable-http", "sse"]) -> None:
    print("Starting MCP server...")
    mcp = get_mcp_server(host=host, port=port)

    # When using "sse", the url will be http://localhost:10001/sse
    # When using "streamable-http", the url will be http://localhost:10001/mcp
    # stdio isn't supported in this example, since rogue won't be able to connect to it.
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
