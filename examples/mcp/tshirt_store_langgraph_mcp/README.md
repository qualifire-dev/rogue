# T-Shirt Store MCP Example (LangGraph)

## Overview

This example demonstrates how to wrap a LangGraph agent with the Model Context Protocol (MCP) to enable communication with Rogue. The agent is a simple t-shirt store assistant built with LangGraph that can check inventory and send emails. By wrapping it with MCP, we can evaluate the agent's security and behavior using Rogue's red-teaming capabilities.

## Our Agent

The agent is implemented in `shirtify_agent.py` using LangGraph's `create_react_agent` function. It's a ReAct-style agent with two tools (`inventory` and `send_email`), uses memory checkpointing for conversation state, and returns structured responses indicating whether the task is complete, requires user input, or encountered an error. The agent has strict instructions to only sell t-shirts at $19.99 with no discounts or promotions.

## MCP Wrapper

The MCP wrapper (`mcp_agent_wrapper.py`) bridges the agent to the MCP protocol using FastMCP. It exposes a single `send_message` tool that extracts the session ID from the request (either from headers or query params) and forwards messages to our LangGraph agent. The wrapper handles session management by passing the session ID to the agent's memory checkpointer, ensuring conversation continuity.

## __main__.py

The `__main__.py` file provides a CLI entry point using Click. It accepts parameters for host, port, and transport type (streamable-http or sse), then starts the MCP server. The server exposes the agent at either `/mcp` (for streamable-http) or `/sse` (for Server-Sent Events), making it accessible to Rogue for evaluation.

