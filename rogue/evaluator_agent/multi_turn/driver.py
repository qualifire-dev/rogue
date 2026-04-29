"""Driver-LLM call that generates the next rogue message in a multi-turn run."""

from typing import Any, Dict, Optional

from loguru import logger
from pydantic import BaseModel, Field

from rogue_sdk.types import ChatHistory

from .json_utils import parse_llm_json
from .prompts import DRIVER_PROMPT


class DriverFailure(RuntimeError):
    """Raised when the driver LLM cannot produce a usable next message.

    The caller should abort the scenario instead of substituting filler —
    pretending to make progress with hardcoded text produces useless,
    repetitive transcripts that the judge then scores as if they were real
    (often as a false-positive pass), and hides real configuration
    problems (bad model name, wrong API key, network).
    """


class DriverMessageResult(BaseModel):
    """Next rogue message proposed by the driver LLM."""

    message: str = Field(
        description="The next message to send to the agent under test.",
    )
    rationale: str = Field(default="", description="Short internal reasoning.")
    attach_kwargs: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Structured side-data for THIS turn's call into the target, "
            "extracted by the driver directly from the runbook text. The "
            "driver populates both the key name (e.g. 'file_path') and the "
            "value (e.g. '/tmp/sample.txt') based on what the current step "
            "explicitly mentions. Empty dict on steps that don't need "
            "side-data (greeting / chit-chat / approval)."
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
) -> DriverMessageResult:
    """Ask the driver LLM for the next rogue message.

    Raises ``DriverFailure`` if the LLM call errors or returns unparseable
    output. The caller is expected to end the scenario in that case rather
    than continue with filler — see the class docstring for why.
    """
    from litellm import acompletion

    prompt = DRIVER_PROMPT.format(
        GOAL=goal,
        BUSINESS_CONTEXT=business_context or "(none)",
        CONVERSATION_HISTORY=conversation.model_dump_json(),
        TURN=turn,
        MAX_TURNS=max_turns,
    )

    try:
        # litellm has its own backoff + retry for transient (429 / 5xx /
        # connection) failures. Letting the SDK retry inside the call keeps
        # one network blip from killing the whole scenario, which the
        # earlier no-retry policy did. ``num_retries`` is best-effort — it
        # silently no-ops on providers that already retry internally.
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
            num_retries=3,
        )
    except Exception as exc:
        logger.exception(
            "Driver LLM call failed",
            extra={"model": model, "turn": turn},
        )
        raise DriverFailure(f"driver LLM call failed: {exc}") from exc

    content = response.choices[0].message.content or ""
    parsed = parse_llm_json(content, DriverMessageResult)
    if parsed is None or not parsed.message.strip():
        logger.warning(
            "Driver output unparseable",
            extra={"raw": content[:300], "turn": turn},
        )
        raise DriverFailure(
            f"driver returned unparseable output (turn {turn}): "
            f"{content[:200] or '<empty>'}",
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
