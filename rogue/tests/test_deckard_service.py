"""Unit tests for DeckardService payload construction.

Validates that the conversation traces shipped to the Rogue Security API
have the expected shape for both the policy-eval reporting path
(`report_summary`) and the red-team scan reporting path
(`report_red_team_scan`).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from rogue.server.services.deckard_service import (
    _MAX_CONTENT_BYTES,
    DeckardService,
    _safe_content,
)
from rogue_sdk.types import (
    ChatHistory,
    ChatMessage,
    ConversationEvaluation,
    EvaluationResult,
    EvaluationResults,
    ReportSummaryRequest,
    Scenario,
    ScenarioType,
)


def _make_scenario(name: str = "Test Scenario") -> Scenario:
    return Scenario(
        scenario=name,
        scenario_type=ScenarioType.POLICY,
        expected_outcome="Should refuse",
    )


def _make_conversation(passed: bool = False) -> ConversationEvaluation:
    history = ChatHistory()
    history.add_message(ChatMessage(role="user", content="hi"))
    history.add_message(ChatMessage(role="assistant", content="hello"))
    return ConversationEvaluation(
        messages=history,
        passed=passed,
        reason="because",
    )


class TestSafeContent:
    def test_returns_empty_for_none(self):
        assert _safe_content(None) == ""

    def test_passes_through_short_strings(self):
        assert _safe_content("hi") == "hi"

    def test_truncates_oversize_strings(self):
        big = "a" * (_MAX_CONTENT_BYTES + 100)
        out = _safe_content(big)
        assert out.endswith("…[truncated]")
        # ASCII: 1 byte per char, so length identity holds.
        assert len(out) == _MAX_CONTENT_BYTES + len("…[truncated]")

    def test_truncates_by_bytes_not_chars(self):
        # 4-byte codepoint repeated past the byte cap.
        big = "𝟘" * (_MAX_CONTENT_BYTES // 2)  # ~2x the byte cap
        out = _safe_content(big)
        assert out.endswith("…[truncated]")
        # Encoded body must fit under the cap (suffix is ASCII).
        body = out[: -len("…[truncated]")]
        assert len(body.encode("utf-8")) <= _MAX_CONTENT_BYTES
        # No mojibake — round-trips cleanly.
        body.encode("utf-8").decode("utf-8")

    def test_coerces_non_strings(self):
        assert _safe_content(42) == "42"


class TestReportSummaryConversations:
    """report_summary should include a conversations[] array per conv."""

    def _run(self, results: List[EvaluationResult]) -> dict:
        captured = {}

        def fake_post(url, headers=None, json=None, timeout=None):
            captured["url"] = url
            captured["headers"] = headers
            captured["payload"] = json
            resp = MagicMock()
            resp.ok = True
            resp.json.return_value = {"success": True}
            return resp

        request = ReportSummaryRequest(
            job_id="job-1",
            rogue_security_api_key="rsk_test",
            rogue_security_base_url="http://localhost:3000",
            judge_model="gpt-4",
        )
        eval_results = EvaluationResults(results=results)
        with patch(
            "rogue.server.services.deckard_service.requests.post",
            side_effect=fake_post,
        ):
            DeckardService.report_summary(request, eval_results)
        return captured["payload"]

    def test_payload_includes_conversations_array(self):
        scenario = _make_scenario("Policy X")
        conv = _make_conversation(passed=False)
        result = EvaluationResult(
            scenario=scenario,
            conversations=[conv],
            passed=False,
        )
        payload = self._run([result])

        assert "conversations" in payload
        assert len(payload["conversations"]) == 1
        row = payload["conversations"][0]
        assert row["scenario_name"] == "Policy X"
        assert row["scenario_type"] == "policy"
        assert row["passed"] is False
        assert row["reason"] == "because"
        assert row["metadata"] == {
            "expected_outcome": "Should refuse",
            "attempt_index": 0,
            "attempts_total": 1,
        }
        assert [m["role"] for m in row["messages"]] == ["user", "assistant"]
        assert [m["content"] for m in row["messages"]] == ["hi", "hello"]

    def test_empty_results_produces_empty_conversations(self):
        payload = self._run([])
        assert payload["conversations"] == []

    def test_multiple_conversations_per_scenario(self):
        scenario = _make_scenario("Policy Y")
        result = EvaluationResult(
            scenario=scenario,
            conversations=[
                _make_conversation(passed=True),
                _make_conversation(passed=False),
            ],
            passed=False,
        )
        payload = self._run([result])
        assert len(payload["conversations"]) == 2
        assert [c["passed"] for c in payload["conversations"]] == [True, False]


class TestBuildRedTeamConversations:
    """_build_red_team_conversations groups per-turn logs by session_id."""

    def test_groups_by_session_and_orders_by_turn(self):
        results = SimpleNamespace(
            vulnerability_results=[
                SimpleNamespace(
                    vulnerability_id="prompt-extraction",
                    vulnerability_name="Prompt Extraction",
                ),
            ],
            conversations=[
                {
                    "session_id": "sess-a",
                    "vulnerability_id": "prompt-extraction",
                    "attack_id": "base64",
                    "turn": 2,
                    "message": "second attempt",
                    "response": "still refuse",
                    "evaluation": {"vulnerability_detected": False},
                },
                {
                    "session_id": "sess-a",
                    "vulnerability_id": "prompt-extraction",
                    "attack_id": "base64",
                    "turn": 1,
                    "message": "first attempt",
                    "response": "refuse",
                    "evaluation": {"vulnerability_detected": False},
                },
                {
                    "session_id": "sess-b",
                    "vulnerability_id": "prompt-extraction",
                    "attack_id": "rot13",
                    "turn": 1,
                    "message": "rot13 attempt",
                    "response": "revealed system prompt",
                    "evaluation": {
                        "vulnerability_detected": True,
                        "reason": "leaked",
                    },
                },
            ],
        )

        convos = DeckardService._build_red_team_conversations(results)
        by_session = {c["conversation_id"]: c for c in convos}

        assert set(by_session) == {"sess-a", "sess-b"}

        a = by_session["sess-a"]
        assert a["scenario_name"] == "Prompt Extraction"
        assert a["scenario_type"] == "prompt-extraction"
        assert a["passed"] is True
        assert [m["content"] for m in a["messages"]] == [
            "first attempt",
            "refuse",
            "second attempt",
            "still refuse",
        ]
        assert [m["role"] for m in a["messages"]] == [
            "user",
            "assistant",
            "user",
            "assistant",
        ]

        b = by_session["sess-b"]
        assert b["passed"] is False
        assert b["reason"] == "leaked"
        assert b["metadata"]["vulnerability_detected"] is True
        assert b["metadata"]["attack_id"] == "rot13"

    def test_empty_conversations_returns_empty_list(self):
        results = SimpleNamespace(
            vulnerability_results=[],
            conversations=[],
        )
        assert DeckardService._build_red_team_conversations(results) == []

    def test_missing_conversations_attribute_returns_empty(self):
        results = SimpleNamespace()
        assert DeckardService._build_red_team_conversations(results) == []

    def test_falls_back_to_vulnerability_id_when_name_missing(self):
        results = SimpleNamespace(
            vulnerability_results=[],
            conversations=[
                {
                    "session_id": "x",
                    "vulnerability_id": "unknown-vuln",
                    "attack_id": "a",
                    "turn": 1,
                    "message": "m",
                    "response": "r",
                    "evaluation": {},
                },
            ],
        )
        convos = DeckardService._build_red_team_conversations(results)
        assert convos[0]["scenario_name"] == "unknown-vuln"

    def test_passed_defaults_to_false_without_evaluator_signal(self):
        # No `vulnerability_detected` key anywhere — the evaluator never
        # cleared this session, so it should NOT be reported as passed.
        results = SimpleNamespace(
            vulnerability_results=[],
            conversations=[
                {
                    "session_id": "no-eval",
                    "vulnerability_id": "v",
                    "turn": 1,
                    "message": "hi",
                    "response": "ok",
                    "evaluation": {},
                },
            ],
        )
        convos = DeckardService._build_red_team_conversations(results)
        assert convos[0]["passed"] is False
        assert convos[0]["metadata"]["evaluator_ran"] is False

    def test_passed_true_only_when_evaluator_explicitly_clears(self):
        results = SimpleNamespace(
            vulnerability_results=[],
            conversations=[
                {
                    "session_id": "cleared",
                    "vulnerability_id": "v",
                    "turn": 1,
                    "message": "hi",
                    "response": "ok",
                    "evaluation": {"vulnerability_detected": False},
                },
            ],
        )
        convos = DeckardService._build_red_team_conversations(results)
        assert convos[0]["passed"] is True
        assert convos[0]["metadata"]["evaluator_ran"] is True

    def test_truncates_oversize_message_content(self):
        big = "x" * (_MAX_CONTENT_BYTES + 50)
        results = SimpleNamespace(
            vulnerability_results=[],
            conversations=[
                {
                    "session_id": "s1",
                    "vulnerability_id": "v",
                    "turn": 1,
                    "message": big,
                    "response": "ok",
                    "evaluation": {},
                },
            ],
        )
        convos = DeckardService._build_red_team_conversations(results)
        assert convos[0]["messages"][0]["content"].endswith("…[truncated]")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
