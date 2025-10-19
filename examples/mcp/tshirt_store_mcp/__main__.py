from dotenv import load_dotenv
from mcp_agent_wrapper import mcp

load_dotenv()


def main():
    print("Starting MCP server...")
    mcp.run()


if __name__ == "__main__":
    main()
