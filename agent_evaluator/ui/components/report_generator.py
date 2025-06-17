import gradio as gr
import pandas as pd
from pathlib import Path


def create_report_generator_screen(shared_state: gr.State):
    with gr.Column():
        gr.Markdown("# Test Report")
        with gr.Row():
            refresh_button = gr.Button("Load Latest Report")
        gr.Markdown("## Evaluation Results")
        dataframe_display = gr.DataFrame(interactive=False)
        gr.Markdown("## Summary")
        summary_display = gr.Markdown("No summary generated yet.")

    def load_report_data(state):
        workdir = state.get("workdir")
        if not workdir:
            return pd.DataFrame(), "Working directory not found."

        csv_path = Path(workdir) / "evaluation_results.csv"
        summary_text = "No summary available."
        df = pd.DataFrame()

        if csv_path.exists():
            df = pd.read_csv(csv_path)
            # You can customize the summary based on the results
            # For now, let's just show the raw results from the state
            results = state.get("results", [])
            if results:
                summary_text = "### Agent Evaluation Summary:\n"
                for i, result in enumerate(results):
                    score = result.get("score", "N/A")
                    reasoning = result.get("reasoning", "No reasoning provided.")
                    summary_text += (
                        f"**Scenario {i+1}**: Score {score}/10\n" f"> *{reasoning}*\n\n"
                    )
        else:
            summary_text = "evaluation_results.csv not found."

        return df, summary_text

    return dataframe_display, summary_display, refresh_button


def setup_report_generator_logic(
    tabs_component, dataframe_display, summary_display, refresh_button, shared_state
):
    def load_report_data(state):
        workdir = state.get("workdir")
        if not workdir:
            return pd.DataFrame(), "Working directory not found."

        csv_path = Path(workdir) / "evaluation_results.csv"
        summary_text = "No summary available."
        df = pd.DataFrame()

        if csv_path.exists():
            df = pd.read_csv(csv_path)
            results = state.get("results", [])
            if results:
                summary_text = "### Agent Evaluation Summary:\n"
                # Simple conversion of results to markdown
                summary_text += "\n\n".join(
                    [
                        f"**Scenario {i+1}** (Passed: {res.get('evaluation_passed', 'N/A')})\n"
                        f"> {res.get('reason', 'No reason provided.')}"
                        for i, res in enumerate(results)
                    ]
                )

        else:
            summary_text = "evaluation_results.csv not found."

        return df, summary_text

    def on_report_tab_select(state):
        df, summary = load_report_data(state)
        return {
            dataframe_display: gr.update(value=df),
            summary_display: gr.update(value=summary),
        }

    report_tab = next(
        (t for t in tabs_component.children if t.id == "report"),
        None,
    )

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
