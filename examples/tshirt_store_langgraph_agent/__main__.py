import logging

import click
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv

from shirtify_langgraph_agent_executor import ShirtifyAgentExecutor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10002)
@click.option("--model", "model", default="openai:gpt-4o")
def main(host, port, model):
    skill = AgentSkill(
        id="sell_tshirt",
        name="Sell T-Shirt",
        description="Helps with selling T-Shirts",
        tags=["sell"],
        examples=["sell a T-Shirt"],
    )

    agent_card = AgentCard(
        name="Shirtify TShirt Store Agent",
        description="Sells Shirtify T-Shirts",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=ShirtifyAgentExecutor(agent_model=model),
        task_store=InMemoryTaskStore(),
    )
    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    import uvicorn

    uvicorn.run(
        a2a_app.build(),
        host=host,
        port=port,
    )


if __name__ == "__main__":
    main()
