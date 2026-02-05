"""
Run Evaluator Agent.

Entry point for running policy-based scenario evaluation.
Red team evaluation is now handled by the server's red_teaming module.
"""

import asyncio
from asyncio import Queue
from typing import TYPE_CHECKING, Any, AsyncGenerator, Optional

from loguru import logger
from rogue_sdk.types import (
    AuthType,
    EvaluationMode,
    EvaluationResults,
    Protocol,
    Scenarios,
    Transport,
)

from ..common.agent_sessions import create_session
from .evaluator_agent_factory import get_evaluator_agent

if TYPE_CHECKING:
    from google.adk.runners import Runner
    from google.adk.sessions import Session


async def _run_agent(
    agent_runner: "Runner",
    input_text: str,
    session: "Session",
) -> str:
    """Run the agent with given input and return the response."""
    from google.genai.types import Content, Part

    input_text_preview = (
        input_text[:100] + "..." if len(input_text) > 100 else input_text
    )
    logger.info(f"🎯 running agent with input: '{input_text_preview}'")

    # Create content from user input
    content = Content(
        role="user",
        parts=[Part(text=input_text)],
    )

    agent_output = ""
    event_count = 0

    logger.info("🔄 Starting agent runner event loop")
    try:
        async for event in agent_runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=content,
        ):
            event_count += 1
            logger.info(f"📨 Agent event #{event_count} received")

            if not event or not event.content or not event.content.parts:
                logger.info(f"⚠️ Event #{event_count} has no content, skipping")
                continue

            event_text = ""
            for part in event.content.parts:
                if part.text:
                    event_text += part.text

            if event_text:
                agent_output += event_text
                logger.info(f"📝 Agent response #{event_count}: {event_text[:100]}...")

            if event.is_final_response():
                logger.info(f"🏁 Agent completed after {event_count} events")
                break

        logger.debug(
            f"✅ _run_agent completed. Total output length: {len(agent_output)}",
        )
    except Exception:
        logger.exception("💥 agent run failed")
        raise

    return agent_output


async def arun_evaluator_agent(
    protocol: Protocol,
    transport: Optional[Transport],
    evaluated_agent_url: str,
    auth_type: AuthType,
    auth_credentials: Optional[str],
    judge_llm: str,
    judge_llm_api_key: Optional[str],
    scenarios: Scenarios,
    business_context: str,
    deep_test_mode: bool,
    judge_llm_aws_access_key_id: Optional[str] = None,
    judge_llm_aws_secret_access_key: Optional[str] = None,
    judge_llm_aws_region: Optional[str] = None,
    evaluation_mode: EvaluationMode = EvaluationMode.POLICY,
    python_entrypoint_file: Optional[str] = None,
    judge_llm_api_base: Optional[str] = None,
    judge_llm_api_version: Optional[str] = None,
) -> AsyncGenerator[tuple[str, Any], None]:
    """
    Run the evaluator agent for policy-based evaluation.

    Note: Red team evaluation is now handled by evaluation_orchestrator
    using the server's red_teaming module. This function only handles
    policy-based scenario evaluation.

    Args:
        protocol: Communication protocol (A2A or MCP)
        transport: Transport mechanism
        evaluated_agent_url: URL of the agent to evaluate
        auth_type: Authentication type
        auth_credentials: Authentication credentials
        judge_llm: LLM to use for evaluation
        judge_llm_api_key: API key for judge LLM
        scenarios: Scenarios to test
        business_context: Business context for the target agent
        deep_test_mode: Enable deep testing mode
        judge_llm_aws_access_key_id: AWS access key ID for judge LLM
        judge_llm_aws_secret_access_key: AWS secret access key for judge LLM
        judge_llm_aws_region: AWS region for judge LLM
        evaluation_mode: Should be POLICY for this function

    Yields:
        Tuple of (update_type, data) where update_type is "chat" or "results"
    """
    # ADK imports take a while, importing them here to reduce startup time
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    logger.info(
        "🤖 arun_evaluator_agent starting",
        extra={
            "protocol": protocol.value,
            "transport": transport.value if transport else None,
            "evaluated_agent_url": evaluated_agent_url,
            "auth_type": auth_type.value,
            "judge_llm": judge_llm,
            "scenario_count": len(scenarios.scenarios),
            "deep_test_mode": deep_test_mode,
        },
    )

    # Red team evaluation should be handled by evaluation_orchestrator
    if evaluation_mode == EvaluationMode.RED_TEAM:
        logger.warning(
            "Red team evaluation should be handled by evaluation_orchestrator, "
            "not run_evaluator_agent",
        )
        yield "results", EvaluationResults()
        return

    try:
        headers = auth_type.get_auth_header(auth_credentials)

        update_queue: Queue = Queue()
        results_queue: Queue = Queue()

        logger.info("🌐 Creating evaluator agent")
        evaluator_agent = get_evaluator_agent(
            protocol=protocol,
            transport=transport,
            evaluated_agent_address=evaluated_agent_url,
            judge_llm=judge_llm,
            scenarios=scenarios,
            business_context=business_context,
            headers=headers,
            judge_llm_auth=judge_llm_api_key,
            judge_llm_aws_access_key_id=judge_llm_aws_access_key_id,
            judge_llm_aws_secret_access_key=judge_llm_aws_secret_access_key,
            judge_llm_aws_region=judge_llm_aws_region,
            judge_llm_api_base=judge_llm_api_base,
            judge_llm_api_version=judge_llm_api_version,
            debug=False,
            deep_test_mode=deep_test_mode,
            chat_update_callback=update_queue.put_nowait,
            python_entrypoint_file=python_entrypoint_file,
        )

        async with evaluator_agent as evaluator_agent:
            # Create ADK session and runner
            session_service = InMemorySessionService()
            app_name = "evaluator_agent"

            logger.info("🏃 Creating ADK Runner")
            runner = Runner(
                app_name=app_name,
                agent=evaluator_agent.get_underlying_agent(),
                session_service=session_service,
            )

            logger.info("🔗 Creating session")
            session = await create_session(
                app_name=app_name,
                session_service=session_service,
            )

            logger.info("🚀 Starting evaluator agent runner task")

            async def agent_runner_task():
                logger.info("🎯 Agent runner task starting")
                try:
                    # Run the agent with start command
                    await _run_agent(runner, "start", session)
                    logger.info("✅ Agent run completed")

                    results = evaluator_agent.get_evaluation_results()
                    logger.info(
                        f"📊 Got evaluation results: "
                        f"{len(results.results) if results.results else 0} results",
                    )
                    await results_queue.put(results)
                except Exception:
                    logger.exception(
                        "💥 Agent runner task failed",
                        extra={
                            "judge_llm": judge_llm,
                            "judge_llm_has_api_key": bool(judge_llm_api_key),
                            "judge_llm_api_base": judge_llm_api_base,
                            "judge_llm_api_version": judge_llm_api_version,
                            "judge_llm_aws_region": judge_llm_aws_region,
                            "judge_llm_has_aws_access_key": bool(
                                judge_llm_aws_access_key_id,
                            ),
                            "evaluated_agent_url": evaluated_agent_url,
                            "protocol": protocol.value,
                            "transport": transport.value if transport else None,
                        },
                    )
                    empty_results = EvaluationResults()
                    await results_queue.put(empty_results)

            runner_task = asyncio.create_task(agent_runner_task())
            logger.info("📡 Starting message processing loop")

            message_count = 0
            while not runner_task.done():
                try:
                    message = await asyncio.wait_for(update_queue.get(), timeout=0.1)
                    message_count += 1
                    logger.info(
                        f"💬 Received chat message #{message_count}: "
                        f"{str(message)[:100]}...",
                    )
                    yield "chat", message
                except asyncio.TimeoutError:
                    continue

            logger.info(
                f"🏁 Message processing loop completed. Total messages: {message_count}",
            )

            # Get final results
            logger.info("📋 Getting final results")
            final_results = await results_queue.get()
            logger.info(
                f"✅ Final results obtained: "
                f"{len(final_results.results) if final_results.results else 0} results",
            )
            yield "results", final_results

            # Check for any runner errors
            try:
                await runner_task
                logger.info("🎉 arun_evaluator_agent completed successfully")
            except Exception as runner_error:
                logger.warning(
                    f"⚠️ Runner task completed with error (handled): {runner_error}",
                )

    except Exception:
        logger.exception(
            "💥 arun_evaluator_agent failed",
            extra={
                "evaluated_agent_url": evaluated_agent_url,
                "judge_llm": judge_llm,
            },
        )
        raise


def run_evaluator_agent(
    protocol: Protocol,
    transport: Optional[Transport],
    evaluated_agent_url: str,
    auth_type: AuthType,
    auth_credentials: Optional[str],
    judge_llm: str,
    judge_llm_api_key: Optional[str],
    scenarios: Scenarios,
    business_context: str,
    deep_test_mode: bool,
) -> EvaluationResults:
    """Synchronous wrapper for arun_evaluator_agent."""

    async def run_evaluator_agent_task():
        async for update_type, data in arun_evaluator_agent(
            protocol=protocol,
            transport=transport,
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
