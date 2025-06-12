import gradio as gr

from ..services.llm_service import LLMService


def create_scenario_generator_screen(shared_state: gr.State, tabs_component: gr.Tabs):
    llm_service = LLMService()

    with gr.Column():
        gr.Markdown("## Scenario Generation")
        business_context_display = gr.Textbox(
            label="Finalized Business Context",
            lines=5,
            interactive=False,
        )
        # When the tab is selected, update the context display
        # This requires a new way to trigger this, let's use a button for now.
        refresh_button = gr.Button("Refresh Context", variant="secondary")

        scenarios_output = gr.JSON(label="Generated Scenarios")
        generate_button = gr.Button("Generate Scenarios")

    def update_context_display(state):
        return state.get("business_context", "")

    def generate_and_display_scenarios(state):
        context = state.get("business_context")
        if not context:
            gr.Warning("Business context is empty. Please finalize it first.")
            return state, None, gr.update()

        judge_llm = state.get("config", {}).get("judge_llm", "openai/o3-mini")
        judge_llm_api_key = state.get("config", {}).get("judge_llm_api_key")

        try:
            scenarios = llm_service.generate_scenarios(
                judge_llm,
                context,
                llm_provider_api_key=judge_llm_api_key,
            )
            state["scenarios"] = scenarios
            gr.Info("Scenarios generated successfully!")
            return (
                state,
                scenarios.model_dump_json(indent=2, exclude_none=True),
                gr.Tabs(selected="run"),
            )
        except Exception:
            gr.Error("Failed to generate scenarios from LLM response.")
            return (
                state,
                {"error": "Failed to generate scenarios."},
                gr.update(),
            )

    refresh_button.click(
        fn=update_context_display,
        inputs=[shared_state],
        outputs=[business_context_display],
    )

    generate_button.click(
        fn=generate_and_display_scenarios,
        inputs=[shared_state],
        outputs=[shared_state, scenarios_output, tabs_component],
    )

    return [business_context_display, generate_button, scenarios_output]
