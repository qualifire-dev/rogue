import gradio as gr
import pandas as pd
from pathlib import Path


def _load_report_data_from_files(
    workdir: Path | None, results: list
) -> tuple[pd.DataFrame, str]:
    if not workdir:
        return pd.DataFrame(), "Working directory not found."

    csv_path = Path(workdir) / "evaluation_results.csv"
    summary_text = "No summary available."
    df = pd.DataFrame()

    if csv_path.exists():
        df = pd.read_csv(csv_path)
        if results:
            summary_text = "### Agent Evaluation Summary:\n"
            summary_text += "\n\n".join(
                [
                    f"**Scenario {i+1}** (Passed: {res.get('evaluation_passed', 'N/A')})\n"
                    f"> {res.get('reason', 'No reason provided.')}"
                    for i, res in enumerate(results)
                ]
            )

    else:
        summary_text = f"evaluation_results.csv not found in {workdir}."

    return df, summary_text


def create_report_generator_screen(shared_state: gr.State):
    with gr.Column():
        gr.Markdown("# Test Report")
        with gr.Row():
            refresh_button = gr.Button("Load Latest Report")
        gr.Markdown("## Evaluation Results")
        dataframe_display = gr.DataFrame(interactive=False)
        gr.Markdown("## Summary")
        summary_display = gr.Markdown("No summary generated yet.")

    return dataframe_display, summary_display, refresh_button


def setup_report_generator_logic(
    tabs_component, dataframe_display, summary_display, refresh_button, shared_state
):
    def on_report_tab_select(state):
        workdir = state.get("workdir")
        results = state.get("results", [])
        df, summary = _load_report_data_from_files(workdir, results)
        return {
            dataframe_display: gr.update(value=df),
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
            outputs=[dataframe_display, summary_display],
        )

    refresh_button.click(
        fn=on_report_tab_select,
        inputs=[shared_state],
        outputs=[dataframe_display, summary_display],
    )
