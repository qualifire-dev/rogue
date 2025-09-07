import pytest
from rogue_sdk.types import (
    ChatHistory,
    ChatMessage,
    ConversationEvaluation,
    EvaluationResult,
    EvaluationResults,
    Scenario,
)


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
                    results=[get_evaluation_result(scenario_1, conversation_1_passed)]
                ),
            ),
            # no overlap from non-empty results
            (
                EvaluationResults(
                    results=[get_evaluation_result(scenario_1, conversation_1_passed)]
                ),
                get_evaluation_result(scenario_2, conversation_1_failed),
                EvaluationResults(
                    results=[
                        get_evaluation_result(scenario_1, conversation_1_passed),
                        get_evaluation_result(scenario_2, conversation_1_failed),
                    ]
                ),
            ),
            # scenario overlap with passed unchanged True -> True
            (
                EvaluationResults(
                    results=[get_evaluation_result(scenario_1, conversation_1_passed)]
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
                    ]
                ),
            ),
            # scenario overlap with passed changed True -> False
            (
                EvaluationResults(
                    results=[get_evaluation_result(scenario_1, conversation_1_passed)]
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
                    ]
                ),
            ),
            # scenario overlap with passed unchanged False -> False (#1)
            (
                EvaluationResults(
                    results=[get_evaluation_result(scenario_1, conversation_1_failed)]
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
                    ]
                ),
            ),
            # scenario overlap with passed unchanged False -> False (#2)
            (
                EvaluationResults(
                    results=[get_evaluation_result(scenario_1, conversation_1_failed)]
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
                    ]
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
