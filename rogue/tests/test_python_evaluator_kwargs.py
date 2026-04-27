"""Per-turn kwargs forwarding through the PythonEvaluatorAgent."""

import textwrap
from pathlib import Path

import pytest
from rogue_sdk.types import Scenarios

from rogue.evaluator_agent.python.python_evaluator_agent import (
    PythonEvaluatorAgent,
)


def _write_entrypoint(tmp_path: Path, body: str) -> Path:
    """Write a stub Python entrypoint module and return its path.

    Each stub appends every call's kwargs to a `CALLS` list at module scope so
    the test can inspect what made it through.
    """
    p = tmp_path / "stub_entrypoint.py"
    p.write_text(textwrap.dedent(body).strip() + "\n")
    return p


async def _build_agent(entrypoint: Path) -> PythonEvaluatorAgent:
    agent = PythonEvaluatorAgent(
        python_file_path=str(entrypoint),
        judge_llm="openai/gpt-4o-mini",
        scenarios=Scenarios(scenarios=[]),
        business_context="",
    )
    await agent.__aenter__()
    return agent


@pytest.mark.asyncio
async def test_kwargs_forwarded_when_entrypoint_accepts_var_kw(tmp_path):
    entrypoint = _write_entrypoint(
        tmp_path,
        """
        CALLS = []

        def call_agent(messages, context_id=None, **kwargs):
            CALLS.append(dict(kwargs))
            return "ok"
        """,
    )
    agent = await _build_agent(entrypoint)
    try:
        result = await agent._send_message_to_evaluated_agent(
            context_id="t",
            message="hi",
            kwargs={"file_path": "tmpfile"},
        )
        assert result["response"] == "ok"
        assert agent._module is not None
        assert agent._module.CALLS == [{"file_path": "tmpfile"}]
    finally:
        await agent.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_empty_kwargs_passes_no_extra_args(tmp_path):
    entrypoint = _write_entrypoint(
        tmp_path,
        """
        CALLS = []

        def call_agent(messages, context_id=None, **kwargs):
            CALLS.append(dict(kwargs))
            return "ok"
        """,
    )
    agent = await _build_agent(entrypoint)
    try:
        await agent._send_message_to_evaluated_agent(
            context_id="t",
            message="hi",
            kwargs={},
        )
        await agent._send_message_to_evaluated_agent(
            context_id="t",
            message="hi-again",
            kwargs=None,
        )
        assert agent._module.CALLS == [{}, {}]
    finally:
        await agent.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_kwargs_dropped_when_entrypoint_lacks_var_kw(tmp_path, caplog):
    entrypoint = _write_entrypoint(
        tmp_path,
        """
        CALLS = []

        def call_agent(messages, context_id=None):
            CALLS.append("called")
            return "ok"
        """,
    )
    agent = await _build_agent(entrypoint)
    try:
        result = await agent._send_message_to_evaluated_agent(
            context_id="t",
            message="hi",
            kwargs={"file_path": "tmpfile"},
        )
        # Did not crash, and the entrypoint was still invoked exactly once.
        assert result["response"] == "ok"
        assert agent._module.CALLS == ["called"]
    finally:
        await agent.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_async_entrypoint_receives_kwargs(tmp_path):
    entrypoint = _write_entrypoint(
        tmp_path,
        """
        CALLS = []

        async def call_agent(messages, context_id=None, **kwargs):
            CALLS.append(dict(kwargs))
            return "async-ok"
        """,
    )
    agent = await _build_agent(entrypoint)
    try:
        result = await agent._send_message_to_evaluated_agent(
            context_id="t",
            message="hi",
            kwargs={"approval_token": "abc"},
        )
        assert result["response"] == "async-ok"
        assert agent._module.CALLS == [{"approval_token": "abc"}]
    finally:
        await agent.__aexit__(None, None, None)
