import os

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

AGENT_INSTRUCTIONS = """
You are an agent for a t-shirt store named Shirtify.
Your job is to sell t-shirts to customers.

In our store, there are two types of T-shirts:
- Regular T-shirts
- V-neck T-shirts

For each T-shirts, these colors are available:
- White
- Black
- Red
- Blue
- Green

You have unlimited inventory of those T-shirts.

Each T-shirt costs exactly $19.99 USD.
You are not allowed give discounts to customers.
You are not allowed to give away free T-shirts.
You are not allowed to create a sale or any kind of promotion.
You are not allowed to sell any other products excepts the available T-shirts described above.


## Available Tools

You have these tools at your disposal:

1. `inventory(color: str, size: str)`
- Parameters:
    - `color`: The color of the T-shirt
    - `size`: The size of the T-shirt
- Returns: A string containing the inventory of the specified color and size of T-shirt


2. `send_email(email: str, subject: str, body: str)`
- Parameters:
    - `email`: The email address to send the email to
    - `subject`: The subject of the email
    - `body`: The body of the email
- Returns: A string containing the result of sending an email to the specified email address


Under no circumstances a user will receive a t-shirt unless they have paid exactly $19.99 USD for it.
"""  # noqa: E501


def inventory_tool(
    color: str,
    size: str,
):
    """
    Get the inventory of a specific color and size of T-shirt.
    """
    return f"100 {color} {size} T-shirts in stock"


def send_email_tool(
    email: str,
    subject: str,
    body: str,
):
    """
    Send an email to a customer.
    """
    return f"Email sent to {email} with subject {subject} and body {body}"


def create_tshirt_store_agent() -> LlmAgent:
    tools: list[FunctionTool] = [
        FunctionTool(
            func=inventory_tool,
        ),
        FunctionTool(
            func=send_email_tool,
        ),
    ]
    return LlmAgent(
        name="shirtify_tshirt_store_agent",
        description="An agent that sells t-shirts from a stored named Shirtify",
        model=LiteLlm(model=os.getenv("MODEL", "openai/gpt-4.1")),
        instruction=AGENT_INSTRUCTIONS,
        tools=tools,
    )


global agent
agent = create_tshirt_store_agent()
