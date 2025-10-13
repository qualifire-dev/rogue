from dotenv import load_dotenv
from mcp_agent_wrapper import mcp

load_dotenv()


def main():
    mcp.run()


if __name__ == "__main__":
    main()
