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

from qualinvest_service_agent import create_investify_service_agent  # type: ignore
from qualinvest_service_agent_executor import investifyAgentExecutor

load_dotenv()

logging.basicConfig()


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10001)
def main(host: str, port: int) -> None:
    skill = AgentSkill(
        id="buy_stocks",
        name="buy stocks",
        description="buy stocks for the user",
        tags=["buy"],
        examples=["buy aapl for 10000$"],
    )
    skill2 = AgentSkill(
        id="check_balance",
        name="check balance",
        description="check user's balance",
        tags=["balance"],
        examples=["do I have available 10000$ to invest in shitcoins"],
    )

    agent_card = AgentCard(
        name="investify service agent",
        description="customer service for investify finance",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill, skill2],
    )

    investify_service_agent = create_investify_service_agent()
    runner = Runner(
        app_name=agent_card.name,
        agent=investify_service_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    agent_executor = investifyAgentExecutor(runner, agent_card)

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
