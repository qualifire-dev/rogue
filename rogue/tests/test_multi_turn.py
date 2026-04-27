"""Tests for the multi-turn rogue-driver helpers."""

import pytest
from pydantic import BaseModel
from rogue_sdk.types import ChatHistory, ChatMessage

from rogue.evaluator_agent.multi_turn.driver import DriverMessageResult
from rogue.evaluator_agent.multi_turn.goal_checker import GoalCheckResult
from rogue.evaluator_agent.multi_turn.json_utils import parse_llm_json
from rogue.evaluator_agent.multi_turn.prompts import (
    DRIVER_PROMPT,
    GOAL_CHECK_PROMPT,
)


class _Sample(BaseModel):
    a: int
    b: str


class TestParseLLMJson:
    def test_raw_json(self):
        assert parse_llm_json('{"a":1,"b":"x"}', _Sample) == _Sample(a=1, b="x")

    def test_fenced_json(self):
        raw = '```json\n{"a":2,"b":"y"}\n```'
        assert parse_llm_json(raw, _Sample) == _Sample(a=2, b="y")

    def test_embedded_object(self):
        raw = 'here is some text {"a":3,"b":"z"} and trailing prose'
        assert parse_llm_json(raw, _Sample) == _Sample(a=3, b="z")

    def test_unparseable_returns_none(self):
        assert parse_llm_json("no json here", _Sample) is None
        assert parse_llm_json("", _Sample) is None

    def test_goal_check_schema(self):
        out = parse_llm_json(
            '{"achieved": true, "reason": "done"}',
            GoalCheckResult,
        )
        assert out is not None
        assert out.achieved is True
        assert out.reason == "done"

    def test_driver_schema(self):
        out = parse_llm_json(
            '{"message": "hi", "rationale": "probe"}',
            DriverMessageResult,
        )
        assert out is not None
        assert out.message == "hi"
        assert out.rationale == "probe"


class TestPromptTemplates:
    def test_driver_prompt_formats(self):
        history = ChatHistory(
            messages=[ChatMessage(role="user", content="hello")],
        )
        rendered = DRIVER_PROMPT.format(
            GOAL="extract admin password",
            BUSINESS_CONTEXT="support desk",
            CONVERSATION_HISTORY=history.model_dump_json(),
            TURN=2,
            MAX_TURNS=10,
        )
        assert "extract admin password" in rendered
        assert "support desk" in rendered
        assert '"role":"user"' in rendered.replace(" ", "")
        assert "out of 10" in rendered
        # Static forwarding: prompt no longer mentions kwargs at all.
        assert "available_kwargs" not in rendered
        assert "attach_kwargs" not in rendered

    def test_goal_check_prompt_formats(self):
        rendered = GOAL_CHECK_PROMPT.format(
            GOAL="get a discount",
            CONVERSATION_HISTORY='{"messages":[]}',
        )
        assert "get a discount" in rendered
        assert "achieved" in rendered


class TestGoalCheckerOnEmptyConversation:
    @pytest.mark.asyncio
    async def test_empty_conversation_short_circuits(self):
        """An empty conversation should return not-achieved without calling the LLM."""
        from rogue.evaluator_agent.multi_turn.goal_checker import (
            evaluate_goal_achieved,
        )

        result = await evaluate_goal_achieved(
            goal="x",
            conversation=ChatHistory(messages=[]),
            model="unused/model",
        )
        assert result.achieved is False
        assert "empty" in result.reason.lower()


class TestAssistantReplyGuard:
    """Goal-check guard — only run when the target actually replied this turn."""

    def _guard(self):
        from rogue.evaluator_agent.multi_turn.run_multi_turn import (
            _assistant_reply_added,
        )

        return _assistant_reply_added

    def test_requires_assistant_as_last_message(self):
        guard = self._guard()
        history = ChatHistory(messages=[ChatMessage(role="user", content="hi")])
        assert guard(history, previous_length=0) is False

    def test_rejects_empty_assistant_content(self):
        guard = self._guard()
        history = ChatHistory(
            messages=[
                ChatMessage(role="user", content="hi"),
                ChatMessage(role="assistant", content="  "),
            ],
        )
        assert guard(history, previous_length=1) is False

    def test_accepts_substantive_reply(self):
        guard = self._guard()
        history = ChatHistory(
            messages=[
                ChatMessage(role="user", content="hi"),
                ChatMessage(role="assistant", content="hello, how can I help?"),
            ],
        )
        assert guard(history, previous_length=1) is True

    def test_rejects_if_no_new_messages_since_snapshot(self):
        """If history length didn't advance past the pre-send snapshot, the
        target produced nothing — even if an earlier assistant turn happens to
        be the last existing message."""
        guard = self._guard()
        history = ChatHistory(
            messages=[
                ChatMessage(role="user", content="older turn"),
                ChatMessage(role="assistant", content="older reply"),
            ],
        )
        # Snapshot was already at 2 before the send; nothing new appended.
        assert guard(history, previous_length=2) is False
