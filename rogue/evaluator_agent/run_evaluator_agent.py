import asyncio
from asyncio import Queue
from typing import AsyncGenerator, Any

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
from ..models.config import AuthType, get_auth_header
from ..models.evaluation_result import EvaluationResults
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
        if not event or not event.content or not event.content.parts:
            continue

        event_text = ""
        for part in event.content.parts:
            if part.text:
                event_text += part.text

        if event_text:
            agent_output += event_text
            logger.debug(f"evaluator_agent response: {event_text}")

        if event.is_final_response():
            logger.debug("evaluator_agent done")
            break  # Without this, this loop will be infinite

    return agent_output


async def arun_evaluator_agent(
    evaluated_agent_url: str,
    auth_type: AuthType,
    auth_credentials: str | None,
    judge_llm: str,
    judge_llm_api_key: str | None,
    scenarios: Scenarios,
    business_context: str,
    deep_test_mode: bool,
) -> AsyncGenerator[tuple[str, Any], None]:
    headers = get_auth_header(auth_type, auth_credentials)
    update_queue: Queue = Queue()
    results_queue: Queue = Queue()

    async with AsyncClient(headers=headers) as httpx_client:
        evaluator_agent = EvaluatorAgent(
            http_client=httpx_client,
            evaluated_agent_address=evaluated_agent_url,
            model=judge_llm,
            scenarios=scenarios,
            llm_auth=judge_llm_api_key,
            business_context=business_context,
            chat_update_callback=update_queue.put_nowait,
            deep_test_mode=deep_test_mode,
        )

        session_service = InMemorySessionService()

        app_name = "Evaluator_Agent"

        runner = Runner(
            app_name=app_name,
            agent=evaluator_agent.get_underlying_agent(),
            session_service=session_service,
        )

        session = await create_session(
            app_name=app_name,
            session_service=session_service,
        )

        logger.debug("evaluator_agent started")

        async def agent_runner_task():
            # This task just runs the agent and puts the final result on a
            # separate queue
            await _run_agent(runner, "start", session)
            results = evaluator_agent.get_evaluation_results()
            await results_queue.put(results)

        runner_task = asyncio.create_task(agent_runner_task())

        while not runner_task.done():
            try:
                # wait for a chat message, but with a timeout
                message = await asyncio.wait_for(update_queue.get(), timeout=0.1)
                yield "chat", message
            except asyncio.TimeoutError:
                continue

        # once runner_task is done, get the final result
        final_results = await results_queue.get()
        yield "results", final_results

        await runner_task  # check for exceptions


def run_evaluator_agent(
    evaluated_agent_url: str,
    auth_type: AuthType,
    auth_credentials: str | None,
    judge_llm: str,
    judge_llm_api_key: str | None,
    scenarios: Scenarios,
    business_context: str,
    deep_test_mode: bool,
) -> EvaluationResults:
    async def run_evaluator_agent_task():
        async for update_type, data in arun_evaluator_agent(
            evaluated_agent_url=evaluated_agent_url,
            auth_type=auth_type,
            auth_credentials=auth_credentials,
            judge_llm=judge_llm,
            judge_llm_api_key=judge_llm_api_key,
            scenarios=scenarios,
            business_context=business_context,
            deep_test_mode=deep_test_mode,
        ):
            if update_type == "results":
                return data

    return asyncio.run(run_evaluator_agent_task())
