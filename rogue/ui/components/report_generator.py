from pathlib import Path
from typing import TYPE_CHECKING, Tuple

from loguru import logger
from rogue_sdk.types import EvaluationResults

from ...server.services.api_format_service import convert_with_structured_summary

if TYPE_CHECKING:
    from gradio import JSON, Markdown, State


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
    shared_state: "State",
) -> Tuple["JSON", "Markdown"]:
    # gradio import takes a while, importing here to reduce startup time.
    import gradio as gr

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
    # gradio import takes a while, importing here to reduce startup time.
    import gradio as gr

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

        # Convert to new API format for display using server service
        try:
            # Extract configuration and additional metadata from state
            config = state.get("config", {})

            # For now, pass None for structured_summary since UI still uses
            # string summaries. This will be updated when the UI summary generation
            # is converted to structured format
            api_format_results = convert_with_structured_summary(
                evaluation_results=results,
                structured_summary=state.get("structured_summary"),
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
