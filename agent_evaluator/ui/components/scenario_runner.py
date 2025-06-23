import json
from datetime import datetime

import gradio as gr
from loguru import logger
from pydantic import ValidationError, HttpUrl

from ...models.config import AuthType
from ...models.scenario import Scenarios
from ...services.llm_service import LLMService
from ...services.scenario_evaluation_service import ScenarioEvaluationService


def create_scenario_runner_screen(shared_state: gr.State, tabs_component: gr.Tabs):
    with gr.Column():
        gr.Markdown("## Scenario Runner & Evaluator")
        scenarios_display = gr.Code(
            label="Scenarios to Run",
            language="json",
            interactive=True,
        )
        status_box = gr.Textbox(
            label="Execution Status",
            lines=10,
            interactive=False,
        )
        run_button = gr.Button("Run Scenarios")

    def update_scenarios_in_state(
        scenarios_string,
        state,
    ):
        try:
            scenarios_json = json.loads(
                scenarios_string,
            )
            state["scenarios"] = scenarios_json
            logger.info("Updated scenarios in state from editable code block.")
        except json.JSONDecodeError:
            logger.error("Invalid JSON in scenarios input.")
            gr.Warning("Could not save, invalid JSON format.")
        return state

    scenarios_display.blur(
        fn=update_scenarios_in_state,
        inputs=[scenarios_display, shared_state],
        outputs=[shared_state],
    )

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
        except (ValidationError, AttributeError):
            return (
                state,
                "Scenarios are misconfigured. "
                "Please check the JSON format and regenerate them if needed.",
                gr.update(),
            )

        agent_url: HttpUrl = config.get("agent_url")  # type: ignore
        agent_auth_type: AuthType | str = config.get("auth_type")  # type: ignore
        agent_auth_credentials: str = config.get("auth_credentials")  # type: ignore
        service_llm: str = config.get("service_llm")  # type: ignore
        judge_llm: str = config.get("judge_llm")  # type: ignore
        judge_llm_key: str = config.get("judge_llm_api_key")  # type: ignore
        business_context: str = config.get("business_context")  # type: ignore

        logger.info(f"Business context: {business_context}")

        if isinstance(agent_auth_type, str):
            agent_auth_type = AuthType(agent_auth_type)
        if agent_auth_credentials == "":
            agent_auth_credentials = None
        if judge_llm_key == "":
            judge_llm_key = None

        status_updates = "Starting execution...\n"
        state["results"] = []  # Clear previous results

        yield state, status_updates, gr.update()

        try:
            workdir = state.get("workdir")
            output_path = (
                workdir / f"evaluation_results_{datetime.now().isoformat()}.json"
            )
            state["evaluation_results_output_path"] = output_path
            evaluation_service = ScenarioEvaluationService(
                evaluated_agent_url=str(agent_url),
                evaluated_agent_auth_type=agent_auth_type,
                evaluated_agent_auth_credentials=agent_auth_credentials,
                judge_llm=judge_llm,
                judge_llm_api_key=judge_llm_key,
                scenarios=scenarios,
                evaluation_results_output_path=output_path,
                business_context=business_context,
            )

            final_results = None
            for update in evaluation_service.evaluate_scenarios():
                if isinstance(update, str):
                    status_updates += f"{update}\n"
                    yield state, status_updates, gr.update()
                else:
                    final_results = update

            logger.debug(
                "scenario runner finished running evaluator agent",
                extra={
                    "results": final_results.model_dump_json() if final_results else {}
                },
            )

            # Generate summary
            summary = LLMService().generate_summary_from_results(
                model=service_llm,
                results=final_results,
                llm_provider_api_key=judge_llm_key,
            )
            state["summary"] = summary
            state["results"] = final_results

        except Exception:
            logger.exception("Error running evaluator agent")
            yield (
                state,
                "Error evaluating scenarios.",
                gr.update(),
            )
            return

        status_updates += "\nEvaluation completed."
        # Final update after loop completes
        yield state, status_updates, gr.update(selected="report")

    run_button.click(
        fn=run_and_evaluate_scenarios,
        inputs=[shared_state],
        outputs=[
            shared_state,
            status_box,
            tabs_component,
        ],
    )

    return scenarios_display, status_box, run_button
