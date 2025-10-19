import asyncio
from asyncio import Queue
from typing import TYPE_CHECKING, Any, AsyncGenerator

from google.genai import types
from loguru import logger
from rogue_sdk.types import AuthType, EvaluationResults, Scenarios, TransportType

from ..common.agent_sessions import create_session
from .evaluator_agent import get_evaluator_agent

if TYPE_CHECKING:
    from google.adk.runners import Runner
    from google.adk.sessions import Session


async def _run_agent(
    agent_runner: "Runner",
    input_text: str,
    session: "Session",
) -> str:
    input_text_preview = (
        input_text[:100] + "..." if len(input_text) > 100 else input_text
    )
    logger.info(f"🎯 running agent with input: '{input_text_preview}'")

    # Create content from user input
    content = types.Content(
        role="user",
        parts=[types.Part(text=input_text)],
    )

    agent_output = ""
    event_count = 0

    logger.info("🔄 Starting agent runner event loop")
    # Run the agent with the runner
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
                break  # Without this, this loop will be infinite

        logger.debug(
            f"✅ _run_agent completed. Total output length: {len(agent_output)}",
        )
    except Exception:
        logger.exception("💥 agent run failed")
        raise

    return agent_output


async def arun_evaluator_agent(
    transport: TransportType,
    evaluated_agent_url: str,
    auth_type: AuthType,
    auth_credentials: str | None,
    judge_llm: str,
    judge_llm_api_key: str | None,
    scenarios: Scenarios,
    business_context: str,
    deep_test_mode: bool,
) -> AsyncGenerator[tuple[str, Any], None]:
    # adk imports take a while, importing them here to reduce rogue startup time.
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService

    logger.info(
        "🤖 arun_evaluator_agent starting",
        extra={
            "evaluated_agent_url": evaluated_agent_url,
            "auth_type": auth_type.value,
            "judge_llm": judge_llm,
            "scenario_count": len(scenarios.scenarios),
            "deep_test_mode": deep_test_mode,
            "business_context_length": len(business_context),
        },
    )

    try:
        headers = auth_type.get_auth_header(auth_credentials)

        update_queue: Queue = Queue()
        results_queue: Queue = Queue()

        logger.info("🌐 Creating evaluator agent")
        evaluator_agent = get_evaluator_agent(
            transport=transport,
            evaluated_agent_address=evaluated_agent_url,
            judge_llm=judge_llm,
            scenarios=scenarios,
            business_context=business_context,
            headers=headers,
            judge_llm_auth=judge_llm_api_key,
            debug=False,
            deep_test_mode=deep_test_mode,
            chat_update_callback=update_queue.put_nowait,
        )

        async with evaluator_agent as evaluator_agent:
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
                    await _run_agent(runner, "start", session)
                    logger.info("✅ Agent runner completed successfully")
                    results = evaluator_agent.get_evaluation_results()
                    logger.info(
                        (
                            "📊 Got evaluation results: "
                            f"{len(results.results) if results.results else 0} results"
                        ),
                    )
                    await results_queue.put(results)
                except Exception:
                    logger.exception("💥 Agent runner task failed")
                    # Put empty results so the evaluation can complete gracefully
                    empty_results = EvaluationResults()
                    await results_queue.put(empty_results)
                    # Don't re-raise, let the evaluation complete with empty results

            runner_task = asyncio.create_task(agent_runner_task())
            logger.info("📡 Starting message processing loop")

            message_count = 0
            while not runner_task.done():
                try:
                    # wait for a chat message, but with a timeout
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

            # once runner_task is done, get the final result
            logger.info("📋 Getting final results")
            final_results = await results_queue.get()
            logger.info(
                (
                    f"✅ Final results obtained: "
                    f"{len(final_results.results) if final_results.results else 0} "
                    "results"
                ),
            )
            yield "results", final_results

            # Check if the runner task had exceptions (but don't re-raise them)
            try:
                await runner_task
                logger.info("🎉 arun_evaluator_agent completed successfully")
            except Exception as runner_error:
                logger.warning(
                    "⚠️ Runner task completed with error (already handled): "
                    f"{runner_error}",
                )
                # Don't re-raise - we already yielded results

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
