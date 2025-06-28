import json
import asyncio
import numpy as np
from datetime import datetime
from pathlib import Path

import gradio as gr
from loguru import logger
from pydantic import ValidationError

from ...models.config import AuthType
from ...models.evaluation_result import EvaluationResults
from ...models.scenario import Scenarios
from ...services.llm_service import LLMService
from ...services.scenario_evaluation_service import ScenarioEvaluationService

MAX_PARALLEL_RUNS = 10


def split_into_batches(scenarios: list, n: int) -> list[list]:
    if not scenarios:
        return []
    if n <= 0:
        raise ValueError("Number of batches must be positive.")
    return [arr.tolist() for arr in np.array_split(scenarios, n) if arr.size > 0]


def create_scenario_runner_screen(shared_state: gr.State, tabs_component: gr.Tabs):
    with gr.Column():
        gr.Markdown("## Scenario Runner & Evaluator")
        with gr.Accordion("scenarios to Run"):
            scenarios_display = gr.Code(
                language="json",
                interactive=True,
            )

        output_components = []
        status_boxes = []
        chat_displays = []

        for i in range(MAX_PARALLEL_RUNS):
            with gr.Group(visible=False) as output_group:
                with gr.Accordion(f"Run {i + 1}"):
                    status_box = gr.Textbox(
                        label=f"Execution Status (Run {i + 1})",
                        lines=2,
                        interactive=False,
                    )
                    live_chat_display = gr.Chatbot(
                        label=f"Live Evaluation Chat (Run {i + 1})",
                        height=300,
                        type="messages",
                    )
                    status_boxes.append(status_box)
                    chat_displays.append(live_chat_display)
            output_components.append(output_group)
            output_components.append(status_box)
            output_components.append(live_chat_display)

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

    async def run_and_evaluate_scenarios(state):
        # --- Create a list of "no-op" updates for all components ---
        def get_blank_updates():
            return [gr.update() for _ in range(len(output_components) + 1)]

        # 1. --- Configuration and Validation ---
        config = state.get("config", {})
        scenarios_json = state.get("scenarios")

        # Hide all runners and clear values
        initial_updates = get_blank_updates()
        for i in range(MAX_PARALLEL_RUNS):
            initial_updates[i * 3] = gr.update(visible=False)  # Group
            initial_updates[i * 3 + 1] = gr.update(value="", visible=True)  # Status
            initial_updates[i * 3 + 2] = gr.update(value=None, visible=True)  # Chat
        yield tuple(initial_updates)

        if not config or not scenarios_json:
            gr.Warning("Config or scenarios not found. Please complete previous steps.")
            return

        try:
            scenarios_model = Scenarios.model_validate(scenarios_json)
        except (ValidationError, AttributeError):
            gr.Warning(
                "Scenarios are misconfigured. Please "
                "check the JSON format and regenerate."
            )
            return

        # 2. --- Setup Parallel Execution ---
        parallel_runs = config.get("parallel_runs", 1)
        scenario_batches = split_into_batches(scenarios_model.scenarios, parallel_runs)
        num_runners = len(scenario_batches)
        update_queue = asyncio.Queue()

        # Make the required number of runners visible
        visibility_updates = get_blank_updates()
        for i in range(num_runners):
            visibility_updates[i * 3] = gr.update(visible=True)
        yield tuple(visibility_updates)

        # 3. --- Define and Run Worker Tasks ---
        async def worker(batch: list, worker_id: int):
            worker_state = state.copy()
            worker_config = worker_state.get("config", {})
            auth_type_val = worker_config.get("auth_type")
            if isinstance(auth_type_val, str):
                auth_type_val = AuthType(auth_type_val)

            try:
                service = ScenarioEvaluationService(
                    evaluated_agent_url=str(worker_config.get("agent_url")),
                    evaluated_agent_auth_type=auth_type_val,
                    evaluated_agent_auth_credentials=worker_config.get(
                        "auth_credentials"
                    ),
                    judge_llm=worker_config.get("judge_llm"),
                    judge_llm_api_key=worker_config.get("judge_llm_api_key"),
                    scenarios=Scenarios(scenarios=batch),
                    evaluation_results_output_path=Path(
                        f"{worker_state.get('workdir')}/temp_results_{worker_id}.json"
                    ),
                    business_context=worker_state.get("business_context"),
                    deep_test_mode=worker_config.get("deep_test_mode", False),
                )

                async for update_type, data in service.evaluate_scenarios():
                    await update_queue.put((worker_id, update_type, data))

            except Exception as e:
                logger.error(f"Error in worker {worker_id}: {e}")
                await update_queue.put((worker_id, "status", f"Error: {e}"))
                await update_queue.put((worker_id, "done", None))

        [
            asyncio.create_task(worker(batch, i))
            for i, batch in enumerate(scenario_batches)
        ]

        # 4. --- Process Updates from Queue ---
        finished_workers = 0
        all_results = EvaluationResults()
        worker_histories = [[] for _ in range(num_runners)]

        while finished_workers < num_runners:
            worker_id, update_type, data = await update_queue.get()

            updates = get_blank_updates()
            if update_type == "status":
                updates[worker_id * 3 + 1] = gr.update(value=data)
            elif update_type == "chat":
                role = "user" if data["role"] == "Evaluator Agent" else "assistant"
                worker_histories[worker_id].append(
                    {"role": role, "content": data["content"]}
                )
                updates[worker_id * 3 + 2] = gr.update(
                    value=worker_histories[worker_id]
                )
            elif update_type == "done":
                finished_workers += 1
                if data:
                    all_results.combine(data)
                updates[worker_id * 3 + 1] = gr.update(
                    value="Finished.", interactive=False
                )
            yield tuple(updates)

        # 5. --- Finalize and Summarize ---
        logger.info("All evaluation runs completed.")
        workdir = state.get("workdir")
        final_output_path = (
            workdir / f"evaluation_results_{datetime.now().isoformat()}.json"
        )
        final_output_path.write_text(all_results.model_dump_json(indent=2))

        summary = LLMService().generate_summary_from_results(
            model=config.get("service_llm"),
            results=all_results,
            llm_provider_api_key=config.get("judge_llm_api_key"),
        )

        state["results"] = all_results
        state["summary"] = summary
        state["evaluation_results_output_path"] = final_output_path

        final_ui_update = get_blank_updates()
        final_ui_update[-1] = gr.update(selected="report")
        yield tuple(final_ui_update)

    run_button.click(
        fn=run_and_evaluate_scenarios,
        inputs=[shared_state],
        outputs=output_components + [tabs_component],
    )

    return scenarios_display, run_button
