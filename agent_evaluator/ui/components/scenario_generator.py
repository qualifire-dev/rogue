import gradio as gr

from ...services.llm_service import LLMService


def create_scenario_generator_screen(shared_state: gr.State, tabs_component: gr.Tabs):
    llm_service = LLMService()

    with gr.Column():
        gr.Markdown("## Scenario Generation")
        business_context_display = gr.Textbox(
            label="Finalized Business Context",
            lines=5,
            interactive=True,
            placeholder="Please provide a brief summary of your agent's business context, including its main goals, user interactions, and key functionalities.",
        )
        scenarios_output = gr.JSON(label="Generated Scenarios")
        generate_button = gr.Button("Generate Scenarios")

    def generate_and_display_scenarios(state, current_context):
        if not current_context:
            gr.Warning("Business context is empty. Please finalize it first.")
            return state, None, gr.update()

        # Update the shared state with the potentially edited context
        state["business_context"] = current_context

        config = state.get("config", {})
        service_llm = config.get("service_llm")
        api_key = config.get("judge_llm_api_key")

        try:
            scenarios = llm_service.generate_scenarios(
                service_llm,
                current_context,
                llm_provider_api_key=api_key,
            )
            state["scenarios"] = scenarios
            return {
                shared_state: state,
                scenarios_output: scenarios.model_dump_json(
                    indent=2, exclude_none=True
                ),
                tabs_component: gr.update(selected="run"),
            }
        except Exception:
            gr.Error("Failed to generate scenarios from LLM response.")
            return {
                shared_state: state,
                scenarios_output: {"error": "Failed to generate scenarios."},
            }

    generate_button.click(
        fn=generate_and_display_scenarios,
        inputs=[shared_state, business_context_display],
        outputs=[shared_state, scenarios_output, tabs_component],
    )

    return [business_context_display, generate_button, scenarios_output]
