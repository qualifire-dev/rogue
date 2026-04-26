"""Entry point for running multi-turn policy scenarios.

Drives the rogue-agent side of the conversation in Python rather than through
ADK, since we need per-turn goal checking and explicit ``max_turns`` semantics.
Reuses the protocol-specific evaluator agents for target I/O and for the final
policy judgment (``_log_evaluation`` → ``evaluate_policy``).
"""

import asyncio
from asyncio import Queue
from typing import Any, AsyncGenerator, Optional
from uuid import uuid4

from loguru import logger
from rogue_sdk.types import (
    AuthType,
    ChatHistory,
    EvaluationResults,
    Protocol,
    Scenarios,
    Transport,
)

from ..evaluator_agent_factory import get_evaluator_agent
from .driver import generate_next_rogue_message
from .goal_checker import evaluate_goal_achieved

_SENTINEL_DONE = object()


async def arun_multi_turn_evaluator(
    protocol: Protocol,
    transport: Optional[Transport],
    evaluated_agent_url: Optional[str],
    auth_type: AuthType,
    auth_credentials: Optional[str],
    judge_llm: str,
    judge_llm_api_key: Optional[str],
    scenarios: Scenarios,
    business_context: str,
    judge_llm_aws_access_key_id: Optional[str] = None,
    judge_llm_aws_secret_access_key: Optional[str] = None,
    judge_llm_aws_region: Optional[str] = None,
    python_entrypoint_file: Optional[str] = None,
    judge_llm_api_base: Optional[str] = None,
    judge_llm_api_version: Optional[str] = None,
) -> AsyncGenerator[tuple[str, Any], None]:
    """Drive multi-turn conversations for the given (already filtered) scenarios.

    Yields ``("chat", dict)`` for each message exchange and a single final
    ``("results", EvaluationResults)``.
    """
    if not scenarios.scenarios:
        logger.info("🟦 multi-turn driver: no scenarios to run")
        yield "results", EvaluationResults()
        return

    logger.info(
        "🟦 multi-turn driver starting",
        extra={
            "scenario_count": len(scenarios.scenarios),
            "judge_llm": judge_llm,
            "protocol": protocol.value,
        },
    )

    headers = auth_type.get_auth_header(auth_credentials)
    update_queue: Queue = Queue()

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
        chat_update_callback=update_queue.put_nowait,
        python_entrypoint_file=python_entrypoint_file,
    )

    llm_kwargs = dict(
        model=judge_llm,
        api_key=judge_llm_api_key,
        aws_access_key_id=judge_llm_aws_access_key_id,
        aws_secret_access_key=judge_llm_aws_secret_access_key,
        aws_region=judge_llm_aws_region,
        api_base=judge_llm_api_base,
        api_version=judge_llm_api_version,
    )

    async with evaluator_agent:

        async def driver_task() -> None:
            try:
                for scenario in scenarios.scenarios:
                    await _drive_one_conversation(
                        evaluator_agent=evaluator_agent,
                        scenario=scenario,
                        business_context=business_context,
                        conversation_index=0,
                        llm_kwargs=llm_kwargs,
                    )
            except Exception:
                logger.exception("💥 multi-turn driver task failed")
            finally:
                await update_queue.put(_SENTINEL_DONE)

        task = asyncio.create_task(driver_task())

        while True:
            msg = await update_queue.get()
            if msg is _SENTINEL_DONE:
                break
            yield "chat", msg

        try:
            await task
        except Exception as runner_err:
            logger.warning(
                f"multi-turn driver task completed with error (handled): {runner_err}",
            )

    results = evaluator_agent.get_evaluation_results()
    logger.info(
        "🏁 multi-turn driver finished",
        extra={"result_count": len(results.results) if results.results else 0},
    )
    yield "results", results


async def _drive_one_conversation(
    evaluator_agent,
    scenario,
    business_context: str,
    conversation_index: int,
    llm_kwargs: dict,
) -> None:
    context_id = uuid4().hex
    goal = scenario.scenario
    max_turns = max(1, scenario.max_turns)

    logger.info(
        "🎬 multi-turn conversation start",
        extra={
            "scenario_preview": goal[:80],
            "max_turns": max_turns,
            "conversation_index": conversation_index,
            "context_id": context_id,
        },
    )

    for turn in range(1, max_turns + 1):
        history = evaluator_agent._context_id_to_chat_history.get(
            context_id,
            ChatHistory(),
        )

        driver_result = await generate_next_rogue_message(
            goal=goal,
            business_context=business_context,
            conversation=history,
            turn=turn,
            max_turns=max_turns,
            **llm_kwargs,
        )

        history_len_before = len(
            evaluator_agent._context_id_to_chat_history.get(
                context_id,
                ChatHistory(),
            ).messages,
        )

        try:
            send_result = await evaluator_agent._send_message_to_evaluated_agent(
                context_id=context_id,
                message=driver_result.message,
            )
        except Exception:
            logger.exception(
                "target agent send failed; ending conversation early",
                extra={"context_id": context_id, "turn": turn},
            )
            break

        if isinstance(send_result, dict) and send_result.get("error"):
            logger.warning(
                "target agent returned error; ending conversation early",
                extra={
                    "context_id": context_id,
                    "turn": turn,
                    "error": send_result.get("error"),
                },
            )
            break

        updated_history = evaluator_agent._context_id_to_chat_history.get(
            context_id,
            ChatHistory(),
        )

        # Only run the goal-check LLM once the target has actually replied to
        # this turn. Each protocol agent appends the user message first, awaits
        # the remote call, and only appends an assistant message when the reply
        # is non-empty; if no assistant reply landed (empty response, streaming
        # that never finalised, etc.) we must not judge the goal against a
        # one-sided history — end the conversation instead.
        if not _assistant_reply_added(
            updated_history,
            previous_length=history_len_before,
        ):
            response_preview = ""
            if isinstance(send_result, dict):
                response_preview = str(send_result.get("response", ""))[:120]
            logger.warning(
                "🟡 target produced no assistant reply this turn; ending "
                "conversation without goal check",
                extra={
                    "context_id": context_id,
                    "turn": turn,
                    "response_preview": response_preview,
                },
            )
            break

        goal_result = await evaluate_goal_achieved(
            goal=goal,
            conversation=updated_history,
            **llm_kwargs,
        )
        if goal_result.achieved:
            logger.info(
                "🎯 goal achieved, stopping conversation",
                extra={"context_id": context_id, "turn": turn},
            )
            break

    # Always log the evaluation so the judge LLM can assess pass/fail against
    # ``expected_outcome``. The bool / reason args are overridden by the judge.
    await asyncio.to_thread(
        evaluator_agent._log_evaluation,
        {
            "scenario": scenario.scenario,
            "scenario_type": scenario.scenario_type.value,
            "expected_outcome": scenario.expected_outcome or "",
        },
        context_id,
        False,
        "multi-turn run complete; awaiting judge",
    )


def _assistant_reply_added(history: ChatHistory, previous_length: int) -> bool:
    """Return True iff the target appended a substantive assistant reply since
    ``previous_length``.

    A turn is only "complete" once the protocol agent has appended an
    assistant-role message with non-empty content to the chat history. We
    compare against the snapshot taken before the send so new user turns (e.g.,
    the rogue's own message) don't masquerade as replies.
    """
    messages = history.messages if history else []
    if len(messages) <= previous_length:
        return False

    last = messages[-1]
    if last.role != "assistant":
        return False
    if not last.content or not last.content.strip():
        return False
    return True
