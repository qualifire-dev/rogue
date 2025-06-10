import gradio as gr
import json
from ..services.a2a_client import A2AClient
from ..services.evaluation_service import EvaluationService


def create_scenario_runner_screen(shared_state: gr.State, tabs_component: gr.Tabs):
    a2a_client = A2AClient()
    evaluation_service = EvaluationService()

    with gr.Column():
        gr.Markdown("## Scenario Runner & Evaluator")
        status_box = gr.Textbox(label="Execution Status", lines=10, interactive=False)
        run_button = gr.Button("Run Scenarios")

    def run_and_evaluate_scenarios(state):
        config = state.get("config", {})
        scenarios = state.get("scenarios", [])

        if not config or not scenarios:
            gr.Warning(
                "Config or scenarios not found. " "Please complete previous steps."
            )
            # The return signature must match the outputs of the click event
            return state, "Missing config or scenarios.", gr.update()

        agent_url = config.get("agent_url")
        judge_llm = config.get("judge_llm")
        judge_llm_key = config.get("judge_llm_api_key")

        status_updates = "Starting execution...\n"
        results = []
        state["results"] = []  # Clear previous results

        yield state, status_updates, gr.update()

        for i, scenario in enumerate(scenarios):
            scenario_name = scenario.get("name", f"Scenario {i+1}")
            status_updates += f"Running: {scenario_name}...\n"
            yield state, status_updates, gr.update()

            scenario_input = scenario.get("inputs", [{}])[0]
            agent_response = a2a_client.send_request(agent_url, scenario_input)

            eval_result = {}
            if "error" in agent_response:
                error_msg = agent_response["error"]
                status_updates += f"  -> FAILED: {error_msg}\n"
                eval_result = {"error": error_msg}
            else:
                expected_output = scenario.get("expected_outputs", [{}])[0]
                eval_result_str = evaluation_service.evaluate_response(
                    judge_llm_model=judge_llm,
                    judge_llm_api_key=judge_llm_key,
                    expected_output=expected_output,
                    agent_response=agent_response,
                )

                try:
                    eval_result = json.loads(eval_result_str)
                    score = eval_result.get("score", "N/A")
                    status_updates += f"  -> COMPLETED. Score: {score}/10\n"
                except json.JSONDecodeError:
                    err_msg = "FAILED: Could not parse evaluation response."
                    status_updates += f"  -> {err_msg}\n"
                    eval_result = {"error": err_msg}

            results.append(eval_result)
            yield state, status_updates, gr.update()

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
