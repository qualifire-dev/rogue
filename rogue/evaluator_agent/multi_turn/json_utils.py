"""Lightweight LLM-JSON parsing helpers for the multi-turn module.

Kept local and minimal; ``policy_evaluation.py`` has its own policy-specific
parser with LLM-repair fallbacks we do not need here.
"""

import json
import re
from typing import Type, TypeVar

from loguru import logger
from pydantic import BaseModel, ValidationError

_T = TypeVar("_T", bound=BaseModel)

_OBJECT_REGEXES = [
    re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL),
    re.compile(r"```\s*(\{.*?\})\s*```", re.DOTALL),
    re.compile(r"(\{.*\})", re.DOTALL),
]


def _strip_fences(output: str) -> str:
    return output.replace("```json", "").replace("```", "").strip()


def parse_llm_json(output: str, model_cls: Type[_T]) -> _T | None:
    """Best-effort parse of an LLM response into a Pydantic model.

    Tries (1) raw JSON, (2) regex-extracted JSON object. Returns ``None`` if
    both strategies fail — callers decide how to react (retry, default, etc).
    """
    if not output:
        return None

    stripped = _strip_fences(output)
    try:
        return model_cls.model_validate_json(stripped)
    except ValidationError:
        pass
    except ValueError:
        pass

    for regex in _OBJECT_REGEXES:
        m = regex.search(stripped)
        if not m:
            continue
        candidate = m.group(1)
        try:
            return model_cls.model_validate_json(candidate)
        except (ValidationError, ValueError):
            try:
                data = json.loads(candidate)
                return model_cls.model_validate(data)
            except (ValidationError, ValueError, json.JSONDecodeError):
                continue

    logger.warning(
        "Failed to parse LLM JSON response",
        extra={
            "model_cls": model_cls.__name__,
            "output_preview": output[:300],
        },
    )
    return None
