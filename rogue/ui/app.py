import json
from pathlib import Path

from rogue_sdk.types import AuthType, Protocol, Transport

from ..common.workdir_utils import load_config
from .components.config_screen import create_config_screen
from .components.interviewer import create_interviewer_screen
from .components.report_generator import (
    create_report_generator_screen,
    setup_report_generator_logic,
)
from .components.scenario_generator import create_scenario_generator_screen
from .components.scenario_runner import create_scenario_runner_screen
from .config.theme import get_theme


def get_app(workdir: Path, rogue_server_url: str):
    # gradio import takes a while, importing here to reduce startup time.
    import gradio as gr

    with gr.Blocks(theme=get_theme(), title="Qualifire Agent Evaluator") as app:
        shared_state = gr.State(
            {
                "config": {},
                "business_context": "",
                "scenarios": [],
                "results": [],
                "workdir": workdir,
                "rogue_server_url": rogue_server_url,
            },
        )

        with gr.Tabs() as tabs:
            with gr.TabItem("1. Config", id="config"):
                (
                    agent_url,
                    protocol,
                    transport,
                    interview_mode,
                    auth_type,
                    auth_credentials,
                    service_llm,
                    judge_llm,
                    judge_llm_api_key,
                    # huggingface_api_key,
                    deep_test_mode,
                    parallel_runs,
                ) = create_config_screen(shared_state, tabs)

            with gr.TabItem("2. Interview", id="interview"):
                create_interviewer_screen(shared_state, tabs)

            with gr.TabItem("3. Scenarios", id="scenarios") as scenarios_tab:
                (
                    business_context_display,
                    _,
                    _,
                ) = create_scenario_generator_screen(shared_state, tabs)

            with gr.TabItem("4. Run & Evaluate", id="run") as run_tab:
                (
                    scenarios_display_runner,
                    _,
                ) = create_scenario_runner_screen(shared_state, tabs)

            with gr.TabItem("5. Report", id="report"):
                (
                    evaluation_results_display,
                    summary_display,
                ) = create_report_generator_screen(shared_state)

        # --- Event Handlers ---
        setup_report_generator_logic(
            tabs,
            evaluation_results_display,
            summary_display,
            shared_state,
        )

        def update_context_display(state):
            return gr.update(value=state.get("business_context", ""))

        scenarios_tab.select(
            fn=update_context_display,
            inputs=[shared_state],
            outputs=[business_context_display],
        )

        def update_scenarios_display(state):
            scenarios = state.get("scenarios", [])
            if scenarios:
                # Scenarios object might be a Pydantic model, so dump it
                if hasattr(scenarios, "model_dump_json"):
                    return scenarios.model_dump_json(indent=2, exclude_none=True)
                return json.dumps(scenarios, indent=2)
            return "{}"

        run_tab.select(
            fn=update_scenarios_display,
            inputs=[shared_state],
            outputs=[scenarios_display_runner],
        )

        def load_and_update_ui():
            state = {
                "business_context": "",
                "scenarios": [],
                "results": [],
                "workdir": workdir,
                "rogue_server_url": rogue_server_url,
            }
            config = load_config(state)
            state["config"] = config

            auth_type_val = config.get(
                "evaluated_agent_auth_type",
                AuthType.NO_AUTH.value,
            )
            protocol_val = Protocol(config.get("protocol", Protocol.A2A))
            transport_val = Transport(config.get("transport", Transport.HTTP))

            if not transport_val.is_valid_for_protocol(protocol_val):
                transport_val = protocol_val.get_default_transport()

            return {
                shared_state: state,
                agent_url: gr.update(
                    value=config.get("evaluated_agent_url", "http://localhost:10001"),
                ),
                protocol: gr.update(value=protocol_val.value),
                transport: gr.update(value=transport_val.value),
                interview_mode: gr.update(value=config.get("interview_mode", True)),
                deep_test_mode: gr.update(value=config.get("deep_test_mode", False)),
                parallel_runs: gr.update(value=config.get("parallel_runs", 1)),
                auth_type: gr.update(value=auth_type_val),
                auth_credentials: gr.update(
                    value=config.get("evaluated_agent_credentials", ""),
                    visible=auth_type_val != AuthType.NO_AUTH.value,
                ),
                service_llm: gr.update(
                    value=config.get("service_llm", "openai/gpt-4.1"),
                ),
                judge_llm: gr.update(value=config.get("judge_llm", "openai/o4-mini")),
                judge_llm_api_key: gr.update(value=config.get("judge_llm_api_key", "")),
                # huggingface_api_key: gr.update(
                #     value=config.get("huggingface_api_key", "")
                # ),
            }

        app.load(
            fn=load_and_update_ui,
            inputs=None,
            outputs=[
                shared_state,
                agent_url,
                protocol,
                transport,
                interview_mode,
                auth_type,
                auth_credentials,
                service_llm,
                judge_llm,
                judge_llm_api_key,
                # huggingface_api_key,
                deep_test_mode,
                parallel_runs,
            ],
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
