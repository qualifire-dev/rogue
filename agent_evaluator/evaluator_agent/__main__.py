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
from httpx import AsyncClient

from .evaluator_agent import EvaluatorAgent
from .evaluator_agent_executor import EvaluatorAgentExecutor
from ..common.configure_logger import configure_logger
from ..config import Config

load_dotenv()

logging.basicConfig()


@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10002)
@click.option(
    "--evaluated-agent-url",
    "evaluated_agent_url",
    default=Config.EvaluatorAgent.EVALUATED_AGENT_URL,
)
@click.option(
    "--authorization",
    "authorization",
    required=False,
    default=None,
    description="Optional authorization header for the evaluated agent",
)
def main(
    host: str,
    port: int,
    evaluated_agent_url: str | None,
    authorization: str | None,
) -> None:
    configure_logger()
    if not evaluated_agent_url:
        raise ValueError("evaluated_agent_url must be provided")

    skill = AgentSkill(
        id="evaluate_agent",
        name="Evaluate Agent",
        description="Evaluate an agent and provide a report",
        tags=["evaluate"],
        examples=["evaluate the agent hosted at http://localhost:10001"],
    )

    agent_card = AgentCard(
        name="Qualifire Agent Evaluator",
        description="Evaluates an agent is working as intended and provides a report",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    headers: dict[str, str] | None = None
    if authorization is not None:
        headers = {"Authorization": authorization}

    httpx_client = AsyncClient(headers=headers)
    evaluator_agent = EvaluatorAgent(
        http_client=httpx_client,
        evaluated_agent_address=evaluated_agent_url,
        model=Config.EvaluatorAgent.MODEL,
    )
    runner = Runner(
        app_name=agent_card.name,
        agent=evaluator_agent.create_agent(),
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    agent_executor = EvaluatorAgentExecutor(runner, agent_card)

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
