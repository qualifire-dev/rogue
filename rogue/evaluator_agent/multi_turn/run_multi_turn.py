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
from .driver import DriverFailure, generate_next_rogue_message
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

    # Legacy scenario-level fallback: file_path / available_kwargs that were
    # set via raw JSON edits to scenarios.json. These are used ONLY on turns
    # where the driver LLM did not extract any side-data — i.e. they're a
    # safety net for back-compat, not a per-key supplement to LLM extraction.
    scenario_fallback_kwargs = scenario.effective_kwargs_pool()
    if scenario_fallback_kwargs:
        logger.debug(
            "scenario carries fallback kwargs (legacy file_path / available_kwargs)",
            extra={
                "context_id": context_id,
                "fallback_keys": list(scenario_fallback_kwargs.keys()),
            },
        )

    # When the target agent is unreachable / errors out / never replies, the
    # conversation cannot be judged meaningfully — record a failure directly
    # instead of asking the judge to score an empty history (which often
    # yields a false-positive pass). See _log_evaluation_failure for details.
    agent_failure_reason: Optional[str] = None

    for turn in range(1, max_turns + 1):
        history = evaluator_agent._context_id_to_chat_history.get(
            context_id,
            ChatHistory(),
        )

        try:
            driver_result = await generate_next_rogue_message(
                goal=goal,
                business_context=business_context,
                conversation=history,
                turn=turn,
                max_turns=max_turns,
                **llm_kwargs,
            )
        except DriverFailure as driver_err:
            # The rogue/driver LLM (which uses the configured judge model)
            # couldn't produce a real next message. Continuing with hardcoded
            # filler would just repeat the same prompt every turn — a useless
            # transcript that the judge then often false-passes. Abort and
            # surface the failure clearly.
            logger.error(
                "💥 rogue driver could not produce a message; aborting scenario",
                extra={
                    "context_id": context_id,
                    "turn": turn,
                    "error": str(driver_err),
                },
            )
            agent_failure_reason = (
                f"Rogue driver LLM ({llm_kwargs.get('model')}) failed on turn "
                f"{turn}: {driver_err}"
            )
            break

        # Defence-in-depth: if the driver returns the exact same message it
        # just sent (model degenerating, prompt-window collapse), we'd loop
        # forever. Treat back-to-back identical user turns as a stuck driver
        # and abort instead of wasting target-LLM tokens on filler.
        if _driver_repeating(history, driver_result.message):
            logger.warning(
                "🟡 rogue driver repeating itself; aborting scenario",
                extra={
                    "context_id": context_id,
                    "turn": turn,
                    "message_preview": driver_result.message[:120],
                },
            )
            agent_failure_reason = (
                f"Rogue driver looped on turn {turn} — repeated the same "
                "message back-to-back. Check the configured judge model."
            )
            break

        resolved_kwargs = _resolve_per_turn_kwargs(
            driver_attach_kwargs=driver_result.attach_kwargs,
            scenario_fallback_kwargs=scenario_fallback_kwargs,
        )
        if resolved_kwargs:
            logger.info(
                "📎 driver attached kwargs to this turn",
                extra={
                    "context_id": context_id,
                    "turn": turn,
                    "kwargs": resolved_kwargs,
                },
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
                kwargs=resolved_kwargs,
            )
        except Exception as send_err:
            logger.exception(
                "target agent send failed; ending conversation early",
                extra={"context_id": context_id, "turn": turn},
            )
            agent_failure_reason = (
                f"Target agent unreachable on turn {turn}: {send_err}"
            )
            break

        if isinstance(send_result, dict) and send_result.get("error"):
            err = send_result.get("error")
            logger.warning(
                "target agent returned error; ending conversation early",
                extra={
                    "context_id": context_id,
                    "turn": turn,
                    "error": err,
                },
            )
            agent_failure_reason = f"Target agent returned error on turn {turn}: {err}"
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
            # Only flag as a failure if no assistant reply has been seen at
            # all during this conversation — if earlier turns produced
            # replies and the target only stopped engaging mid-way, the
            # judge should still get a shot at the partial transcript.
            if turn == 1:
                agent_failure_reason = "Target agent produced no reply on turn 1"
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

    scenario_dict = {
        "scenario": scenario.scenario,
        "scenario_type": scenario.scenario_type.value,
        "expected_outcome": scenario.expected_outcome or "",
    }

    if agent_failure_reason is not None:
        # Target agent never participated — skip the judge entirely so a
        # connection error / 5xx can't be silently scored as "passed".
        await asyncio.to_thread(
            evaluator_agent._log_evaluation_failure,
            scenario_dict,
            context_id,
            agent_failure_reason,
        )
    else:
        # Always log the evaluation so the judge LLM can assess pass/fail
        # against ``expected_outcome``. The bool / reason args are
        # overridden by the judge.
        await asyncio.to_thread(
            evaluator_agent._log_evaluation,
            scenario_dict,
            context_id,
            False,
            "multi-turn run complete; awaiting judge",
        )


def _resolve_per_turn_kwargs(
    driver_attach_kwargs: dict,
    scenario_fallback_kwargs: dict,
) -> dict:
    """Pick the kwargs the runtime forwards into the target this turn.

    Per-turn precedence: when the driver LLM extracted side-data for this
    turn (``driver_attach_kwargs`` non-empty) it is the sole source of
    truth — the legacy fallback is suppressed for the turn so chit-chat /
    approval steps don't leak unrelated legacy keys. When the driver did
    not extract anything, the legacy ``scenario.file_path`` /
    ``scenario.available_kwargs`` (if any) act as the fallback so existing
    JSON-edited scenarios keep working unchanged.

    Returns a fresh dict — caller may mutate it without aliasing either
    input.
    """
    if driver_attach_kwargs:
        return dict(driver_attach_kwargs)
    return dict(scenario_fallback_kwargs)


def _driver_repeating(history: ChatHistory, candidate: str) -> bool:
    """True iff ``candidate`` matches the most recent rogue (user) message.

    A back-to-back duplicate means the driver is stuck — model degenerating,
    bad config, or prompt collapse. Compared case-folded and stripped so a
    trivial whitespace/casing tweak between turns doesn't mask the loop.
    """
    if not candidate or not candidate.strip():
        return False
    messages = history.messages if history else []
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content.strip().casefold() == candidate.strip().casefold()
    return False


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
