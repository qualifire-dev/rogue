from pathlib import Path
from typing import Tuple
from datetime import datetime, timezone

import gradio as gr
from loguru import logger
from rogue_sdk.types import EvaluationResults
from pydantic import BaseModel
from typing import List, Optional
import re


def parse_summary_sections(full_summary: str) -> tuple[str, str, str]:
    """Parse a comprehensive summary into separate sections.

    Args:
        full_summary: The comprehensive summary text

    Returns:
        Tuple of (summary, key_findings, recommendations)
    """
    if not full_summary:
        return None, None, None

    # Extract the main summary section (everything before Key Findings)
    summary_match = re.search(
        r"(.*?)(?=---\s*##?\s+Key Findings|##?\s+Key Findings)",
        full_summary,
        re.DOTALL | re.IGNORECASE,
    )
    summary_section = ""
    if summary_match:
        summary_section = summary_match.group(1).strip()
        # Clean up extra dashes and formatting
        summary_section = re.sub(r"---+\s*$", "", summary_section).strip()

    # Extract Key Findings section
    key_findings_match = re.search(
        r"##?\s+Key Findings\s*[-]*\s*(.*?)(?=---\s*##?\s+Recommendations|##?\s+Recommendations|##?\s+Detailed Breakdown|$)",  # noqa: E501
        full_summary,
        re.DOTALL | re.IGNORECASE,
    )
    key_findings_section = ""
    if key_findings_match:
        key_findings_section = key_findings_match.group(1).strip()
        # Clean up bullet points and formatting
        key_findings_section = re.sub(
            r"^-\s*",
            "",
            key_findings_section,
            flags=re.MULTILINE,
        )
        key_findings_section = re.sub(r"---+\s*$", "", key_findings_section).strip()
        # Fix bullet point formatting
        key_findings_section = re.sub(r"\s*-\s*\*\*", "\n• **", key_findings_section)
        if not key_findings_section.startswith(
            "•",
        ) and not key_findings_section.startswith("-"):
            key_findings_section = "• " + key_findings_section

    # Extract Recommendations section
    recommendations_match = re.search(
        r"##?\s+Recommendations\s*[-]*\s*(.*?)(?=---\s*##?\s+Detailed Breakdown|##?\s+Detailed Breakdown|$)",  # noqa: E501
        full_summary,
        re.DOTALL | re.IGNORECASE,
    )
    recommendations_section = ""
    if recommendations_match:
        recommendations_section = recommendations_match.group(1).strip()
        # Clean up formatting
        recommendations_section = re.sub(
            r"---+\s*$",
            "",
            recommendations_section,
        ).strip()
        # Convert all numbered items to bullet points
        recommendations_section = re.sub(
            r"^\d+\.\s*",
            "• ",
            recommendations_section,
            flags=re.MULTILINE,
        )
        recommendations_section = re.sub(
            r"\s+\d+\.\s*",
            "\n• ",
            recommendations_section,
        )

    return (
        summary_section if summary_section else None,
        key_findings_section if key_findings_section else None,
        recommendations_section if recommendations_section else None,
    )


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

            # Parse the summary to extract separate sections
            if summary and summary != "No summary available.":
                parsed_summary, parsed_key_findings, parsed_recommendations = (
                    parse_summary_sections(summary)
                )
            else:
                parsed_summary = None
                parsed_key_findings = None
                parsed_recommendations = None

            api_format_results = convert_to_api_format(
                evaluation_results=results,
                summary=parsed_summary,
                key_findings=parsed_key_findings or state.get("key_findings"),
                recommendation=parsed_recommendations or state.get("recommendation"),
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
