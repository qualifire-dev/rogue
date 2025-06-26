from pathlib import Path
from typing import Tuple

import gradio as gr
from loguru import logger

from agent_evaluator.models.evaluation_result import EvaluationResults


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
) -> Tuple[gr.Code, gr.Markdown, gr.Button]:
    with gr.Column():
        gr.Markdown("# Test Report")
        with gr.Row():
            refresh_button = gr.Button("Load Latest Report")
        gr.Markdown("## Summary")
        summary_display = gr.Markdown(
            shared_state.value.get("summary_text", "No summary generated yet.")
        )
        gr.Markdown("## Evaluation Results")
        results_display = gr.JSON(label="Evaluation Results")

    return results_display, summary_display, refresh_button


def setup_report_generator_logic(
    tabs_component,
    evaluation_results_display,
    summary_display,
    refresh_button,
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

        return {
            evaluation_results_display: gr.update(
                value=results.model_dump_json(
                    indent=2,
                    exclude_none=True,
                ),
            ),
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

    refresh_button.click(
        fn=on_report_tab_select,
        inputs=[shared_state],
        outputs=[evaluation_results_display, summary_display],
    )
