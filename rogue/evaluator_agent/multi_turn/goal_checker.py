"""Per-turn goal-achievement check via a lightweight LLM call."""

from typing import Optional

from loguru import logger
from pydantic import BaseModel, Field

from rogue_sdk.types import ChatHistory

from .json_utils import parse_llm_json
from .prompts import GOAL_CHECK_PROMPT


class GoalCheckResult(BaseModel):
    """Outcome of a per-turn goal check."""

    achieved: bool = Field(description="Whether the goal has been reached.")
    reason: str = Field(default="", description="Short explanation.")


async def evaluate_goal_achieved(
    goal: str,
    conversation: ChatHistory,
    model: str,
    api_key: Optional[str] = None,
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None,
    aws_region: Optional[str] = None,
    api_base: Optional[str] = None,
    api_version: Optional[str] = None,
) -> GoalCheckResult:
    """Call the judge LLM to assess whether the goal has been achieved.

    Returns a ``GoalCheckResult`` — defaults to ``achieved=False`` on parse or
    API failure so the driver will simply keep going until ``max_turns``.
    """
    from litellm import acompletion

    if not conversation.messages:
        return GoalCheckResult(achieved=False, reason="empty conversation")

    prompt = GOAL_CHECK_PROMPT.format(
        GOAL=goal,
        CONVERSATION_HISTORY=conversation.model_dump_json(),
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
                {"role": "user", "content": "evaluate"},
            ],
            temperature=0,
        )
    except Exception:
        logger.exception(
            "Goal-check LLM call failed; assuming not-achieved",
            extra={"model": model},
        )
        return GoalCheckResult(achieved=False, reason="goal-check call failed")

    content = response.choices[0].message.content or ""
    parsed = parse_llm_json(content, GoalCheckResult)
    if parsed is None:
        logger.warning(
            "Goal-check output unparseable; assuming not-achieved",
            extra={"raw": content[:300]},
        )
        return GoalCheckResult(achieved=False, reason="unparseable goal-check output")

    logger.info(
        "🎯 goal check",
        extra={
            "achieved": parsed.achieved,
            "reason": parsed.reason[:120],
        },
    )
    return parsed
