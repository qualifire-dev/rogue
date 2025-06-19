from pathlib import Path
from typing import Tuple

import gradio as gr

from agent_evaluator.models.evaluation_result import EvaluationResults
from agent_evaluator.services.llm_service import LLMService


def _load_report_data_from_files(
    evaluation_results_output_path: Path | None,
    results: EvaluationResults | None,
    config: dict,
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

    if results and results.results:
        llm_service = LLMService()
        summary_text = llm_service.generate_summary_from_results(
            model=config.get("judge_llm", "default/model"),
            results=results,
            llm_provider_api_key=config.get("judge_llm_api_key"),
        )

    return results, summary_text


def create_report_generator_screen(
    shared_state: gr.State,
) -> Tuple[gr.Code, gr.Markdown, gr.Button]:
    with gr.Column():
        gr.Markdown("# Test Report")
        with gr.Row():
            refresh_button = gr.Button("Load Latest Report")
        gr.Markdown("## Evaluation Results")
        results_display = gr.JSON(
            label="Evaluation Results",
        )
        gr.Markdown("## Summary")
        summary_display = gr.Markdown(
            shared_state.value.get("summary_text", "No summary generated yet.")
        )

    return results_display, summary_display, refresh_button


def setup_report_generator_logic(
    tabs_component,
    evaluation_results_display,
    summary_display,
    refresh_button,
    shared_state,
):
    def on_report_tab_select(state):
        evaluation_results_output_path = state.get("evaluation_results_output_path")
        results = state.get("results", EvaluationResults())
        config = state.get("config", {})
        evaluation_results, summary = _load_report_data_from_files(
            evaluation_results_output_path,
            results,
            config,
        )
        return {
            evaluation_results_display: gr.update(
                value=evaluation_results.model_dump_json(
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
