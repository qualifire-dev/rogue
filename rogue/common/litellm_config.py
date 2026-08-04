"""Single point that opts the rogue *server* into litellm's permissive mode.

Setting ``litellm.drop_params = True`` makes provider-incompatible kwargs
(notably ``temperature`` on gpt-5-family models, ``logprobs`` on most
non-OpenAI providers, etc.) silently dropped instead of raising
``UnsupportedParamsError`` mid-scenario.

This module owns the flag-flip so every caller — the FastAPI server
(``rogue.run_server``) and the local web wrapper (``rogue.run_web``) —
opts in explicitly. We deliberately do NOT set this in ``rogue/__init__.py``
because that's a hostile side effect for any library consumer who imports
``rogue`` for its evaluation primitives without wanting their global
``litellm`` instance silently mutated.
"""

from __future__ import annotations

import os

from loguru import logger

# Agents under test are frequently agentic themselves (tool loops, browsing,
# sub-agents), so a single turn can far outlast a plain chat completion. The
# old hardcoded 30s made those agents look like they were failing when they
# were merely still working.
DEFAULT_AGENT_REQUEST_TIMEOUT = 300.0


def configure_for_server() -> None:
    """Enable litellm's permissive parameter handling for server flows."""
    try:
        import litellm
    except Exception:  # noqa: BLE001 - litellm is a hard dep, but be defensive
        return
    litellm.drop_params = True


def agent_request_timeout() -> float:
    """Per-request timeout, in seconds, for calls to the agent under test.

    Override with ``ROGUE_AGENT_REQUEST_TIMEOUT``. Note this is the timeout for
    a *single* attempt — the underlying OpenAI client retries twice by default,
    so worst-case wall time is roughly three times this value.
    """
    raw = os.getenv("ROGUE_AGENT_REQUEST_TIMEOUT")
    if not raw:
        return DEFAULT_AGENT_REQUEST_TIMEOUT
    try:
        value = float(raw)
    except ValueError:
        logger.warning(
            f"Ignoring non-numeric ROGUE_AGENT_REQUEST_TIMEOUT={raw!r}; "
            f"using {DEFAULT_AGENT_REQUEST_TIMEOUT}s",
        )
        return DEFAULT_AGENT_REQUEST_TIMEOUT
    if value <= 0:
        logger.warning(
            f"Ignoring non-positive ROGUE_AGENT_REQUEST_TIMEOUT={raw!r}; "
            f"using {DEFAULT_AGENT_REQUEST_TIMEOUT}s",
        )
        return DEFAULT_AGENT_REQUEST_TIMEOUT
    return value
