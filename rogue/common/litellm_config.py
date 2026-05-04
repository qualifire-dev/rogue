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


def configure_for_server() -> None:
    """Enable litellm's permissive parameter handling for server flows."""
    try:
        import litellm
    except Exception:  # noqa: BLE001 - litellm is a hard dep, but be defensive
        return
    litellm.drop_params = True
