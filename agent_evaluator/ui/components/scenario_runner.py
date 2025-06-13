import gradio as gr
from loguru import logger
from pydantic import ValidationError, HttpUrl, SecretStr

from ...evaluator_agent.run_evaluator_agent import run_evaluator_agent
from ...models.config import AuthType
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
            scenarios = Scenarios.model_validate(scenarios)
        except ValidationError:
            return (
                state,
                "Scenarios are misconfigured. Please regenerate them in the previous steps.",
                gr.update(),
            )

        agent_url: HttpUrl = config.get("agent_url")  # type: ignore
        agent_auth_type: AuthType = config.get("auth_type")  # type: ignore
        agent_auth_credentials: SecretStr = config.get("auth_credentials")  # type: ignore
        judge_llm: str = config.get("judge_llm")  # type: ignore
        judge_llm_key: SecretStr = config.get("judge_llm_api_key")  # type: ignore

        if agent_auth_credentials is None:
            agent_auth_credentials = SecretStr("")
        if judge_llm_key is None:
            judge_llm_key = SecretStr("")

        status_updates = "Starting execution...\n"
        state["results"] = []  # Clear previous results

        yield state, status_updates, gr.update()

        try:
            results = run_evaluator_agent(
                evaluated_agent_url=str(agent_url),
                auth_type=agent_auth_type,
                auth_credentials=agent_auth_credentials.get_secret_value(),
                judge_llm=judge_llm,
                judge_llm_api_key=judge_llm_key.get_secret_value(),
                scenarios=scenarios,
            )
        except Exception:
            logger.exception("Error running evaluator agent")
            return (
                state,
                "Error evaluating scenarios.",
                gr.update(),
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
