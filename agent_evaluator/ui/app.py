from pathlib import Path

import gradio as gr

from .components.config_screen import create_config_screen
from .components.interviewer import create_interviewer_screen
from .components.report_generator import create_report_generator_screen
from .components.scenario_generator import create_scenario_generator_screen
from .components.scenario_runner import create_scenario_runner_screen
from .config.theme import theme


def get_app(workdir: Path):
    with gr.Blocks(theme=theme, title="Qualifire Agent Evaluator") as app:
        # A single state object to hold all shared data across tabs
        shared_state = gr.State(
            {
                "config": {},
                "business_context": "",
                "scenarios": [],
                "results": [],
                "workdir": workdir,
            }
        )

        with gr.Tabs() as tabs:
            with gr.TabItem("1. Config", id="config"):
                create_config_screen(shared_state, tabs)

            with gr.TabItem("2. Interview", id="interview"):
                create_interviewer_screen(shared_state, tabs)

            with gr.TabItem("3. Scenarios", id="scenarios") as scenarios_tab:
                (
                    business_context_display,
                    _,
                    _,
                ) = create_scenario_generator_screen(shared_state, tabs)

            with gr.TabItem("4. Run & Evaluate", id="run"):
                create_scenario_runner_screen(shared_state, tabs)

            with gr.TabItem("5. Report", id="report"):
                create_report_generator_screen(shared_state)

        def update_context_display(state):
            return gr.update(value=state.get("business_context", ""))

        scenarios_tab.select(
            fn=update_context_display,
            inputs=[shared_state],
            outputs=[business_context_display],
        )

        footer_html = """
        <div style="text-align: center; margin-top: 20px; font-size: 14px;
                    color: #6B63BF;">
            made with ❤️ by <a href="https://qualifire.ai" target="_blank"
                            style="color: #494199; text-decoration: none;">
                                Qualifire
                            </a>
        </div>
        """
        gr.Markdown(footer_html)

        return app
