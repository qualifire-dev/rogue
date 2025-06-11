from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from httpx import AsyncClient
from loguru import logger

from .evaluator_agent import EvaluatorAgentFactory
from ..common.agent_sessions import create_session
from ..models.scenario import Scenarios
from ..ui.models.config import AuthType


def _get_agent_card(host: str, port: int):
    skill = AgentSkill(
        id="evaluate_agent",
        name="Evaluate Agent",
        description="Evaluate an agent and provide a report",
        tags=["evaluate"],
        examples=["evaluate the agent hosted at http://localhost:10001"],
    )

    return AgentCard(
        name="Qualifire Agent Evaluator",
        description="Evaluates an agent is working as intended and provides a report",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )


def _get_headers(
    auth_credentials: str | None,
    auth_type: AuthType,
) -> dict[str, str] | None:
    if auth_type is None or auth_type == AuthType.NO_AUTH or not auth_credentials:
        return None

    prefix = ""
    if auth_type == AuthType.BEARER_TOKEN:
        prefix = "Bearer "
    elif auth_type == AuthType.BASIC_AUTH:
        prefix = "Basic "

    return {"Authorization": prefix + auth_credentials}


def _run_agent(
    agent_runner: Runner,
    input_text: str,
    session: Session | None = None,
) -> str:
    session = session or create_session()

    # Create content from user input
    content = types.Content(
        role="user",
        parts=[types.Part(text=input_text)],
    )

    agent_output = ""

    # Run the agent with the runner
    for event in agent_runner.run(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content,
    ):
        event_text = ""
        for part in event.content.parts:
            event_text += part.text

        agent_output += event_text

        try:
            logger.info(f"evaluator_agent response: {event_text}")
        except Exception:
            pass

        if event.is_final_response():
            logger.info(f"evaluator_agent done")

    return agent_output


async def run_evaluator_agent(
    host: str,
    port: int,
    evaluated_agent_url: str,
    auth_type: AuthType,
    auth_credentials: str | None,
    judge_llm: str,
    scenarios: Scenarios,
) -> str:
    agent_card = _get_agent_card(host, port)
    headers = _get_headers(auth_credentials, auth_type)

    async with AsyncClient(headers=headers) as httpx_client:
        evaluator_agent = EvaluatorAgentFactory(
            http_client=httpx_client,
            evaluated_agent_address=evaluated_agent_url,
            model=judge_llm,
            scenarios=scenarios,
        )
        runner = Runner(
            app_name=agent_card.name,
            agent=evaluator_agent.create_agent(),
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        return _run_agent(runner, input_text="start")
