import pytest
from datetime import datetime
from rogue_sdk.types import (
    ChatHistory,
    ChatMessage,
    ConversationEvaluation,
    EvaluationResult,
    EvaluationResults,
    Scenario,
)
from rogue.server.services.api_format_service import convert_to_api_format
from rogue.server.models.api_format import ApiEvaluationResult, StructuredSummary


class TestEvaluationResults:
    scenario_1 = Scenario(scenario="Scenario 1")
    scenario_2 = Scenario(scenario="Scenario 2")

    conversation_1_passed = ConversationEvaluation(
        messages=ChatHistory(messages=[ChatMessage(role="user", content="message 1")]),
        passed=True,
        reason="reason",
    )
    conversation_2_passed = ConversationEvaluation(
        messages=ChatHistory(messages=[ChatMessage(role="user", content="message 2")]),
        passed=True,
        reason="reason",
    )

    conversation_1_failed = ConversationEvaluation(
        messages=ChatHistory(messages=[ChatMessage(role="user", content="message 1")]),
        passed=False,
        reason="reason",
    )
    conversation_2_failed = ConversationEvaluation(
        messages=ChatHistory(messages=[ChatMessage(role="user", content="message 2")]),
        passed=False,
        reason="reason",
    )

    @staticmethod
    def get_evaluation_result(
        scenario: Scenario,
        conversation: ConversationEvaluation,
    ) -> EvaluationResult:
        return EvaluationResult(
            scenario=scenario,
            conversations=[conversation],
            passed=conversation.passed,
        )

    @pytest.mark.parametrize(
        "existing_results, new_result, expected_results",
        [
            # no overlap from empty results
            (
                EvaluationResults(),
                get_evaluation_result(scenario_1, conversation_1_passed),
                EvaluationResults(
                    results=[get_evaluation_result(scenario_1, conversation_1_passed)],
                ),
            ),
            # no overlap from non-empty results
            (
                EvaluationResults(
                    results=[get_evaluation_result(scenario_1, conversation_1_passed)],
                ),
                get_evaluation_result(scenario_2, conversation_1_failed),
                EvaluationResults(
                    results=[
                        get_evaluation_result(scenario_1, conversation_1_passed),
                        get_evaluation_result(scenario_2, conversation_1_failed),
                    ],
                ),
            ),
            # scenario overlap with passed unchanged True -> True
            (
                EvaluationResults(
                    results=[get_evaluation_result(scenario_1, conversation_1_passed)],
                ),
                get_evaluation_result(scenario_1, conversation_2_passed),
                EvaluationResults(
                    results=[
                        EvaluationResult(
                            scenario=scenario_1,
                            conversations=[
                                conversation_1_passed,
                                conversation_2_passed,
                            ],
                            passed=True,
                        ),
                    ],
                ),
            ),
            # scenario overlap with passed changed True -> False
            (
                EvaluationResults(
                    results=[get_evaluation_result(scenario_1, conversation_1_passed)],
                ),
                get_evaluation_result(scenario_1, conversation_2_failed),
                EvaluationResults(
                    results=[
                        EvaluationResult(
                            scenario=scenario_1,
                            conversations=[
                                conversation_1_passed,
                                conversation_2_failed,
                            ],
                            passed=False,
                        ),
                    ],
                ),
            ),
            # scenario overlap with passed unchanged False -> False (#1)
            (
                EvaluationResults(
                    results=[get_evaluation_result(scenario_1, conversation_1_failed)],
                ),
                get_evaluation_result(scenario_1, conversation_2_failed),
                EvaluationResults(
                    results=[
                        EvaluationResult(
                            scenario=scenario_1,
                            conversations=[
                                conversation_1_failed,
                                conversation_2_failed,
                            ],
                            passed=False,
                        ),
                    ],
                ),
            ),
            # scenario overlap with passed unchanged False -> False (#2)
            (
                EvaluationResults(
                    results=[get_evaluation_result(scenario_1, conversation_1_failed)],
                ),
                get_evaluation_result(
                    scenario_1,
                    conversation_2_passed,
                ),  # passed is ignored here because we already failed
                EvaluationResults(
                    results=[
                        EvaluationResult(
                            scenario=scenario_1,
                            conversations=[
                                conversation_1_failed,
                                conversation_2_passed,
                            ],
                            passed=False,
                        ),
                    ],
                ),
            ),
        ],
    )
    def test_add_result(
        self,
        existing_results: EvaluationResults,
        new_result: EvaluationResult,
        expected_results: EvaluationResults,
    ):
        existing_results.add_result(new_result)
        assert existing_results == expected_results

    def test_convert_to_api_format(self):
        """Test conversion to new API format."""
        results = EvaluationResults()
        result = self.get_evaluation_result(self.scenario_1, self.conversation_1_passed)
        results.add_result(result)

        # Create structured summary for testing
        structured_summary = StructuredSummary(
            overall_summary="Test summary for overall evaluation",
            key_findings=["Key finding 1", "Key finding 2"],
            recommendations=["Recommendation 1", "Recommendation 2"],
            detailed_breakdown=[
                {"scenario": "Test", "status": "✅", "outcome": "Passed"},
            ],
        )

        api_format = convert_to_api_format(
            evaluation_results=results,
            structured_summary=structured_summary,
            deep_test=True,
            judge_model="openai/gpt-4o-mini",
        )

        assert isinstance(api_format, ApiEvaluationResult)
        assert len(api_format.scenarios) == 1
        assert api_format.scenarios[0].description == "Scenario 1"
        assert api_format.scenarios[0].totalConversations == 1
        assert api_format.scenarios[0].flaggedConversations == 0
        assert len(api_format.scenarios[0].conversations) == 1

        # Test structured summary fields
        assert api_format.summary == "Test summary for overall evaluation"
        assert api_format.keyFindings == "• Key finding 1\n• Key finding 2"
        assert api_format.recommendation == "• Recommendation 1\n• Recommendation 2"
        assert api_format.deepTest is True
        assert api_format.judgeModel == "openai/gpt-4o-mini"
        assert api_format.scenarios[0].conversations[0].passed is True
        assert api_format.scenarios[0].conversations[0].reason == "reason"
        assert len(api_format.scenarios[0].conversations[0].messages) == 1

        # Test message conversion
        message = api_format.scenarios[0].conversations[0].messages[0]
        assert message.role == "user"
        assert message.content == "message 1"
        assert isinstance(message.timestamp, datetime)

        # Test new fields
        assert api_format.summary == "Test summary for overall evaluation"
        assert api_format.keyFindings == "• Key finding 1\n• Key finding 2"
        assert api_format.recommendation == "• Recommendation 1\n• Recommendation 2"
        assert api_format.deepTest is True
        assert api_format.judgeModel == "openai/gpt-4o-mini"
        assert isinstance(api_format.startTime, datetime)
