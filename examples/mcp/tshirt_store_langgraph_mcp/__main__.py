from dotenv import load_dotenv

from .mcp_agent_wrapper import mcp

load_dotenv()


def main() -> None:
    print("Starting MCP server...")

    # Can also be "sse".
    # When using "sse", the url will be http://localhost:10001/sse
    # When using "streamable-http", the url will be http://localhost:10001/mcp
    # stdio isn't supported in this example, since rogue won't be able to connect to it.
    mcp.run(transport="streamable-http")
    # mcp.run(transport="sse")


if __name__ == "__main__":
    main()
