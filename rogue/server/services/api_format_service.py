"""Service for converting evaluation results to API format.

This service handles the conversion from legacy EvaluationResults
to the new enhanced API format with structured summary data.
"""

from datetime import datetime, timezone
from typing import Optional

from rogue_sdk.types import EvaluationResults

from ..models.api_format import (
    ApiChatMessage,
    ApiConversationEvaluation,
    ApiEvaluationResult,
    ApiScenarioResult,
    StructuredSummary,
)


def convert_to_api_format(
    evaluation_results: EvaluationResults,
    structured_summary: Optional[StructuredSummary] = None,
    deep_test: bool = False,
    start_time: Optional[datetime] = None,
    judge_model: Optional[str] = None,
) -> ApiEvaluationResult:
    """Convert legacy EvaluationResults to new API format.

    Args:
        evaluation_results: Legacy evaluation results to convert
        structured_summary: Structured summary from LLM with separate sections
        deep_test: Whether deep test mode was enabled
        start_time: When the evaluation started (defaults to current time)
        judge_model: The LLM judge model used

    Returns:
        ApiEvaluationResult: New format evaluation result with additional metadata
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc)

    api_scenarios = []

    for result in evaluation_results.results:
        # Convert conversations to new format
        api_conversations = []
        for conv_eval in result.conversations:
            # Convert ChatHistory messages to ApiChatMessage
            api_messages = []
            for msg in conv_eval.messages.messages:
                timestamp = datetime.now(timezone.utc)
                if msg.timestamp:
                    try:
                        if isinstance(msg.timestamp, str):
                            timestamp = datetime.fromisoformat(
                                msg.timestamp.replace("Z", "+00:00"),
                            )
                        else:
                            timestamp = msg.timestamp
                    except (ValueError, AttributeError):
                        timestamp = datetime.now(timezone.utc)

                api_messages.append(
                    ApiChatMessage(
                        role=msg.role,
                        content=msg.content,
                        timestamp=timestamp,
                    ),
                )

            api_conversations.append(
                ApiConversationEvaluation(
                    passed=conv_eval.passed,
                    messages=api_messages,
                    reason=conv_eval.reason if conv_eval.reason else None,
                ),
            )

        api_scenarios.append(
            ApiScenarioResult(
                description=result.scenario.scenario,
                totalConversations=len(api_conversations),
                flaggedConversations=len(
                    [c for c in api_conversations if not c.passed],
                ),
                conversations=api_conversations,
            ),
        )

    # Extract structured summary components
    summary = None
    key_findings = None
    recommendation = None

    if structured_summary:
        summary = structured_summary.overall_summary
        key_findings = "\n".join(
            f"• {finding}" for finding in structured_summary.key_findings
        )
        recommendation = "\n".join(
            f"• {rec}" for rec in structured_summary.recommendations
        )

    return ApiEvaluationResult(
        scenarios=api_scenarios,
        summary=summary,
        keyFindings=key_findings,
        recommendation=recommendation,
        deepTest=deep_test,
        startTime=start_time,
        judgeModel=judge_model,
    )


def convert_with_structured_summary(
    evaluation_results: EvaluationResults,
    structured_summary: Optional[StructuredSummary] = None,
    deep_test: bool = False,
    start_time: Optional[datetime] = None,
    judge_model: Optional[str] = None,
) -> ApiEvaluationResult:
    """Convert to API format with structured summary.

    Args:
        evaluation_results: Legacy evaluation results to convert
        structured_summary: Structured summary from LLM
        deep_test: Whether deep test mode was enabled
        start_time: When the evaluation started
        judge_model: The LLM judge model used

    Returns:
        ApiEvaluationResult: New format with structured summary data
    """
    return convert_to_api_format(
        evaluation_results=evaluation_results,
        structured_summary=structured_summary,
        deep_test=deep_test,
        start_time=start_time,
        judge_model=judge_model,
    )
