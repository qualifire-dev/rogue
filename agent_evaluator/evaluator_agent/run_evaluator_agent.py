import asyncio
from pathlib import Path

import pandas as pd
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from httpx import AsyncClient
from loguru import logger

from .evaluator_agent import EvaluatorAgent
from ..common.agent_sessions import create_session
from ..models.config import AuthType
from ..models.scenario import Scenarios


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


async def _run_agent(
    agent_runner: Runner,
    input_text: str,
    session: Session,
) -> str:
    # Create content from user input
    content = types.Content(
        role="user",
        parts=[types.Part(text=input_text)],
    )

    agent_output = ""

    # Run the agent with the runner
    async for event in agent_runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content,
    ):
        event_text = ""
        for part in event.content.parts:
            if part.text:
                event_text += part.text

        if event_text:
            agent_output += event_text
            logger.info(f"evaluator_agent response: {event_text}")

        if event.is_final_response():
            logger.info("evaluator_agent done")
            break  # Without this, this loop will be infinite

    return agent_output


async def arun_evaluator_agent(
    # host: str,
    # port: int,
    evaluated_agent_url: str,
    auth_type: AuthType,
    auth_credentials: str | None,
    judge_llm: str,
    judge_llm_api_key: str | None,
    scenarios: Scenarios,
    workdir: Path,
) -> pd.DataFrame:
    # agent_card = _get_agent_card(host, port)
    headers = _get_headers(auth_credentials, auth_type)

    async with AsyncClient(headers=headers) as httpx_client:
        evaluator_agent = EvaluatorAgent(
            http_client=httpx_client,
            evaluated_agent_address=evaluated_agent_url,
            model=judge_llm,
            scenarios=scenarios,
            llm_auth=judge_llm_api_key,
            workdir=workdir,
        )

        session_service = InMemorySessionService()

        app_name = "Evaluator_Agent"

        runner = Runner(
            app_name=app_name,  # agent_card.name,
            agent=evaluator_agent.get_underlying_agent(),
            session_service=session_service,
        )

        session = await create_session(
            app_name=app_name,
            session_service=session_service,
        )

        logger.info("evaluator_agent started")

        await _run_agent(runner, input_text="start", session=session)
        return evaluator_agent.get_results_df()


def run_evaluator_agent(
    # host: str,
    # port: int,
    evaluated_agent_url: str,
    auth_type: AuthType,
    auth_credentials: str | None,
    judge_llm: str,
    judge_llm_api_key: str | None,
    scenarios: Scenarios,
    workdir: Path,
) -> pd.DataFrame:
    return asyncio.run(
        arun_evaluator_agent(
            evaluated_agent_url=evaluated_agent_url,
            auth_type=auth_type,
            auth_credentials=auth_credentials,
            judge_llm=judge_llm,
            judge_llm_api_key=judge_llm_api_key,
            scenarios=scenarios,
            workdir=workdir,
        )
    )
