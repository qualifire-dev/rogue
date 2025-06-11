import gradio as gr


def create_report_generator_screen(shared_state: gr.State):
    with gr.Column():
        gr.Markdown("# Test Report")
        report_display = gr.Markdown("No report generated yet.")
        refresh_button = gr.Button("Load Latest Report")

    def generate_report_from_state(state):
        results = state.get("results", [])
        scenarios = state.get("scenarios", [])

        if not results:
            return "No results found in state. Please run the evaluator."

        full_report = "## Overall Results\n\n"
        # Add summary logic here later

        full_report += "\n## Detailed Scenario Results\n\n"
        for i, result in enumerate(results):
            scenario_name = scenarios[i].get("name", f"Scenario {i+1}")
            score = result.get("score", "N/A")
            reasoning = result.get("reasoning", "N/A")
            full_report += (
                f"### {scenario_name}\n"
                f"- **Score**: {score}/10\n"
                f"- **Reasoning**: {reasoning}\n\n"
            )

        return full_report

    refresh_button.click(
        fn=generate_report_from_state, inputs=[shared_state], outputs=[report_display]
    )

    return [report_display]
