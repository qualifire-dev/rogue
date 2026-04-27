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
    def test_driver_prompt_formats_without_kwargs(self):
        history = ChatHistory(
            messages=[ChatMessage(role="user", content="hello")],
        )
        rendered = DRIVER_PROMPT.format(
            GOAL="extract admin password",
            BUSINESS_CONTEXT="support desk",
            CONVERSATION_HISTORY=history.model_dump_json(),
            TURN=2,
            MAX_TURNS=10,
            AVAILABLE_KWARGS_SECTION="",
            ATTACH_KWARGS_SCHEMA_LINE="",
        )
        assert "extract admin password" in rendered
        assert "support desk" in rendered
        assert '"role":"user"' in rendered.replace(" ", "")
        assert "out of 10" in rendered
        # No kwargs noise when none are available.
        assert "<available_kwargs>" not in rendered
        assert "attach_kwargs" not in rendered

    def test_driver_prompt_renders_runbook_kwargs_section(self):
        from rogue.evaluator_agent.multi_turn.prompts import (
            render_available_kwargs_section,
        )

        section = render_available_kwargs_section(["file_path", "approval_token"])
        rendered = DRIVER_PROMPT.format(
            GOAL="1. say hello\n2. upload the file\n3. confirm",
            BUSINESS_CONTEXT="(none)",
            CONVERSATION_HISTORY="{}",
            TURN=2,
            MAX_TURNS=5,
            AVAILABLE_KWARGS_SECTION=section,
            ATTACH_KWARGS_SCHEMA_LINE=(',\n  "attach_kwargs": [<keys>]'),
        )
        # The pool keys are listed inside the available_kwargs block.
        assert "<available_kwargs>" in rendered
        assert "- file_path" in rendered
        assert "- approval_token" in rendered
        # The schema line is appended to the JSON output spec.
        assert "attach_kwargs" in rendered
        # Worked example references both upload and non-upload turns so the
        # LLM has a concrete pattern to follow.
        assert "Worked example" in rendered
        assert '"attach_kwargs": ["file_path"]' in rendered
        assert '"attach_kwargs": []' in rendered

    def test_render_available_kwargs_section_empty(self):
        from rogue.evaluator_agent.multi_turn.prompts import (
            render_available_kwargs_section,
        )

        assert render_available_kwargs_section([]) == ""

    def test_driver_message_result_parses_attach_kwargs(self):
        out = parse_llm_json(
            '{"message":"ok here is the file","rationale":"upload step",'
            '"attach_kwargs":["file_path"]}',
            DriverMessageResult,
        )
        assert out is not None
        assert out.attach_kwargs == ["file_path"]

    def test_driver_message_result_defaults_attach_kwargs_empty(self):
        # Legacy / no-kwargs scenarios still parse without attach_kwargs in
        # the LLM output.
        out = parse_llm_json(
            '{"message":"hi","rationale":"greeting"}',
            DriverMessageResult,
        )
        assert out is not None
        assert out.attach_kwargs == []

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


class TestPathMentionDetector:
    """Heuristic that warns when a scenario mentions a path but the kwargs
    pool is empty (the customer's ``file_path`` field wasn't filled in)."""

    def _re(self):
        from rogue.evaluator_agent.multi_turn.run_multi_turn import (
            _PATH_MENTION_RE,
        )

        return _PATH_MENTION_RE

    def test_matches_quoted_absolute_path_with_extension(self):
        rx = self._re()
        text = 'User will send a file at "/Users/yanay/a.pdf"'
        assert rx.findall(text) == ["/Users/yanay/a.pdf"]

    def test_matches_unquoted_path(self):
        rx = self._re()
        assert rx.findall("upload /tmp/sample.txt please") == ["/tmp/sample.txt"]

    def test_does_not_match_simple_uri_scheme_paths(self):
        rx = self._re()
        # ``file://`` and similar URI schemes start with ``:/`` which the
        # lookbehind rejects. (Full URLs with ``http://host/path.pdf`` may
        # produce a heuristic false-positive — that's a harmless WARN, not a
        # correctness issue.)
        assert rx.findall("file:///etc/passwd") == []
        # No extension → not a path mention.
        assert rx.findall("plain prose with no path") == []

    def test_no_match_for_plain_prose(self):
        rx = self._re()
        assert rx.findall("please grant a discount of 10%") == []

    def test_multiple_paths(self):
        rx = self._re()
        found = rx.findall("first /a/b.txt then /c/d/e.json")
        assert found == ["/a/b.txt", "/c/d/e.json"]


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
