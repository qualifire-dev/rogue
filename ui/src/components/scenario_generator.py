import gradio as gr
import json
from ..services.llm_service import LLMService
from ..models.scenario import TestScenario

# Commented out as validation is optional
# from ..models.scenario import TestScenario


def create_scenario_generator_screen(shared_state: gr.State, tabs_component: gr.Tabs):
    llm_service = LLMService()

    with gr.Column():
        gr.Markdown("## Scenario Generation")
        business_context_display = gr.Textbox(
            label="Finalized Business Context",
            lines=5,
            interactive=False,
        )
        generate_button = gr.Button("Generate Scenarios")
        scenarios_output = gr.JSON(label="Generated Scenarios")

    def update_context_display(state):
        return state.get("business_context", "")

    def generate_and_display_scenarios(state):
        context = state.get("business_context")
        if not context:
            gr.Warning("Business context is empty. Please finalize it first.")
            return state, None, gr.update()

        judge_llm = state.get("config", {}).get("judge_llm", "openai/o3-mini")
        scenarios_json_str = llm_service.generate_scenarios(judge_llm, context)

        try:
            scenarios_data = json.loads(scenarios_json_str)
            state["scenarios"] = scenarios_data
            gr.Info("Scenarios generated successfully!")
            return state, scenarios_data, gr.Tabs(selected="run")
        except json.JSONDecodeError:
            gr.Error("Failed to parse scenarios from LLM response.")
            return (
                state,
                {"error": "Invalid JSON received from LLM."},
                gr.update(),
            )

    # When the tab is selected, update the context display
    # This requires a new way to trigger this, let's use a button for now.
    refresh_button = gr.Button("Refresh Context", variant="secondary")
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
