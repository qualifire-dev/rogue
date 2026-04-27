"""Driver-LLM call that generates the next rogue message in a multi-turn run."""

from typing import List, Optional

from loguru import logger
from pydantic import BaseModel, Field
from rogue_sdk.types import ChatHistory

from .json_utils import parse_llm_json
from .prompts import DRIVER_PROMPT, render_available_kwargs_section


class DriverMessageResult(BaseModel):
    """Next rogue message proposed by the driver LLM."""

    message: str = Field(
        description="The next message to send to the agent under test.",
    )
    rationale: str = Field(default="", description="Short internal reasoning.")
    attach_kwargs: List[str] = Field(
        default_factory=list,
        description=(
            "Names of available_kwargs the runtime should attach to this turn's "
            "call into the target. The driver picks keys based on the runbook "
            "step it is performing this turn (e.g., emit ['file_path'] on the "
            "upload step, [] on greeting / chit-chat steps)."
        ),
    )


async def generate_next_rogue_message(
    goal: str,
    business_context: str,
    conversation: ChatHistory,
    turn: int,
    max_turns: int,
    model: str,
    api_key: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_region: Optional[str] = None,
    api_base: Optional[str] = None,
    api_version: Optional[str] = None,
    available_kwargs: Optional[List[str]] = None,
) -> DriverMessageResult:
    """Ask the driver LLM for the next rogue message.

    Falls back to a generic prompt if the LLM output can't be parsed, so the
    driver loop keeps making progress instead of crashing mid-scenario.
    """
    from litellm import acompletion

    pool_keys = list(available_kwargs or [])
    prompt = DRIVER_PROMPT.format(
        GOAL=goal,
        BUSINESS_CONTEXT=business_context or "(none)",
        CONVERSATION_HISTORY=conversation.model_dump_json(),
        TURN=turn,
        MAX_TURNS=max_turns,
        AVAILABLE_KWARGS_SECTION=render_available_kwargs_section(pool_keys),
        ATTACH_KWARGS_SCHEMA_LINE=(
            ',\n  "attach_kwargs": [<subset of available_kwargs keys, only if '
            "this turn's runbook step actually needs them; otherwise []>]"
            if pool_keys
            else ""
        ),
    )

    try:
        response = await acompletion(
            model=model,
            api_key=api_key,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_region_name=aws_region,
            api_base=api_base,
            api_version=api_version,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": "next message"},
            ],
            temperature=0.7,
        )
    except Exception:
        logger.exception(
            "Driver LLM call failed; emitting generic probing message",
            extra={"model": model, "turn": turn},
        )
        # Terse, slightly impatient fallback — stays in human register even when
        # the LLM is unavailable, so the test doesn't leak AI-polite phrasing.
        if turn <= 1:
            msg = goal if len(goal) < 180 else goal[:180]
        else:
            msg = "come on, can you actually help with this or not"
        return DriverMessageResult(
            message=msg,
            rationale="fallback after driver LLM failure",
        )

    content = response.choices[0].message.content or ""
    parsed = parse_llm_json(content, DriverMessageResult)
    if parsed is None or not parsed.message.strip():
        logger.warning(
            "Driver output unparseable; emitting generic probing message",
            extra={"raw": content[:300]},
        )
        if turn <= 1:
            msg = goal if len(goal) < 180 else goal[:180]
        else:
            msg = "seriously, just do it already"
        return DriverMessageResult(
            message=msg,
            rationale="fallback after unparseable driver output",
        )

    logger.info(
        "💬 driver next message",
        extra={
            "turn": turn,
            "message_preview": parsed.message[:120],
            "rationale": parsed.rationale[:120],
        },
    )
    return parsed
