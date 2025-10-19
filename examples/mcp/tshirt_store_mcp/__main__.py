from dotenv import load_dotenv
from mcp_agent_wrapper import mcp
from shirtify_agent import ShirtifyAgent

load_dotenv()


def main():
    print("Starting MCP server...")
    mcp.run(transport="sse")


def main2():
    agent = ShirtifyAgent()
    res = agent.invoke("What are you selling?")
    print(res)


if __name__ == "__main__":
    main()
