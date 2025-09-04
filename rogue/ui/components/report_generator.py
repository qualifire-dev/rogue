from pathlib import Path
from typing import Tuple
from datetime import datetime, timezone

import gradio as gr
from loguru import logger
from rogue_sdk.types import EvaluationResults
from pydantic import BaseModel
from typing import List, Optional


# New API Format Types for report display
class ApiChatMessage(BaseModel):
    """Chat message for new API format with datetime timestamp."""

    role: str
    content: str
    timestamp: datetime


class ApiConversationEvaluation(BaseModel):
    """Conversation evaluation for new API format."""

    passed: bool
    messages: List[ApiChatMessage]
    reason: Optional[str] = None


class ApiScenarioResult(BaseModel):
    """Result of evaluating a single scenario in new API format."""

    description: Optional[str] = None
    totalConversations: Optional[int] = None
    flaggedConversations: Optional[int] = None
    conversations: List[ApiConversationEvaluation]


class ApiEvaluationResult(BaseModel):
    """New API format for evaluation results."""

    scenarios: List[ApiScenarioResult]
    summary: Optional[str] = None
    keyFindings: Optional[str] = None
    recommendation: Optional[str] = None
    deepTest: bool = False
    startTime: datetime
    judgeModel: Optional[str] = None


def convert_to_api_format(
    evaluation_results: EvaluationResults,
    summary: Optional[str] = None,
    key_findings: Optional[str] = None,
    recommendation: Optional[str] = None,
    deep_test: bool = False,
    start_time: Optional[datetime] = None,
    judge_model: Optional[str] = None,
) -> ApiEvaluationResult:
    """Convert legacy EvaluationResults to new API format.

    Args:
        evaluation_results: Legacy evaluation results to convert
        summary: Generated summary of the evaluation
        key_findings: Key findings from the evaluation
        recommendation: Recommendations based on the evaluation
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

    return ApiEvaluationResult(
        scenarios=api_scenarios,
        summary=summary,
        keyFindings=key_findings,
        recommendation=recommendation,
        deepTest=deep_test,
        startTime=start_time,
        judgeModel=judge_model,
    )


def _load_report_data_from_files(
    evaluation_results_output_path: Path | None,
    results: EvaluationResults | None,
) -> tuple[EvaluationResults, str]:
    if (
        not evaluation_results_output_path
        or not evaluation_results_output_path.exists()
    ):
        return EvaluationResults(), "Evaluation results file not found."

    summary_text = "No summary available."

    if not results:
        results = EvaluationResults.model_validate_json(
            evaluation_results_output_path.read_text(),
        )

    return results, summary_text


def create_report_generator_screen(
    shared_state: gr.State,
) -> Tuple[gr.JSON, gr.Markdown]:
    with gr.Column():
        gr.Markdown("## Summary")
        summary_display = gr.Markdown(
            shared_state.value.get("summary_text", "No summary generated yet."),
        )
        gr.Markdown("## Evaluation Results")
        results_display = gr.JSON(label="Evaluation Results")

    return results_display, summary_display


def setup_report_generator_logic(
    tabs_component,
    evaluation_results_display,
    summary_display,
    shared_state,
):
    def on_report_tab_select(state):
        results = state.get("results", EvaluationResults())
        summary = state.get("summary", "No summary available.")

        # Ensure results is not a list before calling model_dump_json
        if isinstance(results, list):
            logger.warning(
                "Results is a list, setting to empty EvaluationResults",
                extra={
                    "results": results,
                },
            )
            results = EvaluationResults()

        # Convert to new API format for display
        try:
            # Extract configuration and additional metadata from state
            config = state.get("config", {})

            api_format_results = convert_to_api_format(
                evaluation_results=results,
                summary=summary if summary != "No summary available." else None,
                key_findings=state.get("key_findings"),
                recommendation=state.get("recommendation"),
                deep_test=config.get("deep_test_mode", False),
                start_time=state.get("start_time"),
                judge_model=config.get("judge_llm"),
            )
            results_json = api_format_results.model_dump_json(
                indent=2,
                exclude_none=True,
            )
        except Exception as e:
            logger.warning(
                f"Failed to convert results to API format: {e}",
                extra={
                    "results": results,
                },
            )
            results_json = str(results)

        return {
            evaluation_results_display: gr.update(value=results_json),
            summary_display: gr.update(value=summary),
        }

    # Find the report tab by its id
    report_tab = None
    # HACK: tabs_component is a list of TabItem objects,
    # and we need to find the one with id 'report'
    # This is not ideal, but it's a workaround for how Gradio handles tabs
    for t in tabs_component.children:
        if t.id == "report":
            report_tab = t
            break

    if report_tab:
        report_tab.select(
            fn=on_report_tab_select,
            inputs=[shared_state],
            outputs=[evaluation_results_display, summary_display],
        )
