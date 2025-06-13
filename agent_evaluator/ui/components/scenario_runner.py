import gradio as gr
from pydantic import ValidationError

from ...evaluator_agent.run_evaluator_agent import run_evaluator_agent
from ...models.scenario import Scenarios


def create_scenario_runner_screen(shared_state: gr.State, tabs_component: gr.Tabs):
    with gr.Column():
        gr.Markdown("## Scenario Runner & Evaluator")
        status_box = gr.Textbox(label="Execution Status", lines=10, interactive=False)
        run_button = gr.Button("Run Scenarios")

    def run_and_evaluate_scenarios(state):
        config = state.get("config", {})
        scenarios = state.get("scenarios")

        if not config or not scenarios:
            gr.Warning(
                "Config or scenarios not found. " "Please complete previous steps."
            )
            # The return signature must match the outputs of the click event
            return state, "Missing config or scenarios.", gr.update()

        try:
            Scenarios.model_validate_json(scenarios)
        except ValidationError:
            return (
                state,
                "Scenarios are misconfigured. Please regenerate them in the previous steps.",
                gr.update(),
            )

        agent_url = config.get("agent_url")
        agent_auth_type = config.get("auth_type")
        agent_auth_credentials = config.get("auth_credentials")
        judge_llm = config.get("judge_llm")
        judge_llm_key = config.get("judge_llm_api_key")

        status_updates = "Starting execution...\n"
        results = []
        state["results"] = []  # Clear previous results

        yield state, status_updates, gr.update()

        run_evaluator_agent(
            evaluated_agent_url=agent_url,
            auth_type=agent_auth_type,
            auth_credentials=agent_auth_credentials,
            judge_llm=judge_llm,
            judge_llm_api_key=judge_llm_key,
            scenarios=Scenarios.model_validate_json(scenarios),
        )

        status_updates += "\nAll scenarios complete."
        state["results"] = results
        # Final update after loop completes
        return state, status_updates, gr.Tabs(selected="report")

    run_button.click(
        fn=run_and_evaluate_scenarios,
        inputs=[shared_state],
        outputs=[shared_state, status_box, tabs_component],
    )

    return [status_box, run_button]
