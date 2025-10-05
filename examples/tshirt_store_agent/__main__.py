import logging

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from .tshirt_store_agent import create_tshirt_store_agent
from .tshirt_store_agent_executor import TShirtStoreAgentExecutor

load_dotenv()

logging.basicConfig()


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10001)
def main(host: str, port: int) -> None:
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
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    tshirt_store_agent = create_tshirt_store_agent()
    runner = Runner(
        app_name=agent_card.name,
        agent=tshirt_store_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    agent_executor = TShirtStoreAgentExecutor(runner, agent_card)

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )

    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    uvicorn.run(
        a2a_app.build(),
        host=host,
        port=port,
    )


if __name__ == "__main__":
    main()
