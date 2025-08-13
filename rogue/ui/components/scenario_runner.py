import asyncio
import json

import gradio as gr
from loguru import logger
from pydantic import HttpUrl
from rogue_client import RogueClientConfig, RogueSDK
from rogue_client.types import (
    AgentConfig,
    AuthType,
    EvaluationRequest,
    EvaluationResults,
    Scenario,
    Scenarios,
)

from ...common.workdir_utils import dump_scenarios
from ...services.llm_service import LLMService

MAX_PARALLEL_RUNS = 10


def split_into_batches(scenarios: list, n: int) -> list[list]:
    if not scenarios:
        return []
    if n <= 0:
        raise ValueError("Number of batches must be positive.")

    # Calculate size of each batch
    total = len(scenarios)
    batch_size, remainder = divmod(total, n)

    batches = []
    start = 0
    for i in range(n):
        # Add one extra item to early batches if there's remainder
        end = start + batch_size + (1 if i < remainder else 0)
        if start < total:  # Only add non-empty batches
            batches.append(scenarios[start:end])
        start = end

    return batches


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
            state["scenarios"] = Scenarios.model_validate(scenarios_json)
            logger.info("Updated scenarios in state from editable code block.")
        except json.JSONDecodeError:
            logger.exception("Invalid JSON in scenarios input.")
            gr.Warning("Could not save, invalid JSON format.")
        return state

    scenarios_display.blur(
        fn=update_scenarios_in_state,
        inputs=[scenarios_display, shared_state],
        outputs=[shared_state],
    )

    async def run_and_evaluate_scenarios(state):
        logger.info("🚀 Starting to evaluate scenarios")

        # --- Create a list of "no-op" updates for all components ---
        def get_blank_updates():
            return [gr.update() for _ in range(len(output_components) + 1)]

        # 1. --- Configuration and Validation ---
        config = state.get("config", {})
        scenarios = state.get("scenarios")

        if scenarios is None:
            logger.warning("No scenarios found in state")
            gr.Warning("No scenarios found. Please generate scenarios first.")
            return

        dump_scenarios(state, scenarios)

        scenarios = scenarios.scenarios
        logger.info(f"Number of scenarios to run: {len(scenarios)}")

        # Hide all runners and clear values
        initial_updates = get_blank_updates()
        for i in range(MAX_PARALLEL_RUNS):
            initial_updates[i * 3] = gr.update(visible=False)  # Group
            initial_updates[i * 3 + 1] = gr.update(value="", visible=True)  # Status
            initial_updates[i * 3 + 2] = gr.update(value=None, visible=True)  # Chat
        yield tuple(initial_updates)

        if not config or not scenarios:
            logger.error("Missing config or scenarios")
            gr.Warning("Config or scenarios not found. Please complete previous steps.")
            return

        # 2. --- Setup Parallel Execution ---
        parallel_runs = config.get("parallel_runs", 1)
        logger.info(f"Setting up {parallel_runs} parallel runs")
        scenario_batches = split_into_batches(scenarios, parallel_runs)
        num_runners = len(scenario_batches)
        logger.info(f"Created {num_runners} scenario batches")
        logger.debug(f"Batch sizes: {[len(batch) for batch in scenario_batches]}")

        update_queue = asyncio.Queue()

        # Make the required number of runners visible
        visibility_updates = get_blank_updates()
        for i in range(num_runners):
            visibility_updates[i * 3] = gr.update(visible=True)
            # Add a test status message to see if updates work
            visibility_updates[i * 3 + 1] = gr.update(
                value=f"🔧 Initializing worker {i + 1}..."
            )
        yield tuple(visibility_updates)

        # Add a small delay and test update to verify the UI update mechanism works
        await asyncio.sleep(1)
        test_updates = get_blank_updates()
        for i in range(num_runners):
            test_updates[i * 3 + 1] = gr.update(
                value=f"✅ Worker {i + 1} ready, starting evaluation..."
            )
        yield tuple(test_updates)

        # 3. --- Define and Run Worker Tasks ---
        async def worker(batch: list[Scenario], worker_id: int):
            logger.info(f"🔧 Starting worker {worker_id} with {len(batch)} scenarios")
            worker_state = state.copy()
            worker_config = worker_state.get("config", {})
            auth_type_val = worker_config.get("auth_type")
            if isinstance(auth_type_val, str):
                auth_type_val = AuthType(auth_type_val)

            try:
                # Use SDK for evaluation
                logger.info(f"Worker {worker_id}: Starting SDK evaluation")
                await _worker_with_sdk(
                    batch, worker_id, worker_config, worker_state, update_queue
                )
                logger.info(
                    f"Worker {worker_id}: SDK evaluation completed successfully"
                )

            except Exception as e:
                logger.exception(f"Error in worker {worker_id}")
                await update_queue.put((worker_id, "status", f"Error: {e}"))
                await update_queue.put((worker_id, "done", None))

        async def _worker_with_sdk(
            batch: list[Scenario],
            worker_id: int,
            worker_config: dict,
            worker_state: dict,
            update_queue: asyncio.Queue,
        ):
            """Worker using SDK with real-time WebSocket updates."""
            logger.info(f"🔌 Worker {worker_id}: Initializing SDK connection")
            sdk_config = RogueClientConfig(
                base_url=HttpUrl("http://localhost:8000"),
                timeout=600.0,
            )
            sdk = RogueSDK(sdk_config)

            try:
                # Check server health
                logger.debug(f"Worker {worker_id}: Checking server health")
                await sdk.health()

                await update_queue.put(
                    (
                        worker_id,
                        "status",
                        f"Starting evaluation with SDK (batch size: {len(batch)})",
                    )
                )

                # Convert auth type
                auth_type_val = worker_config.get("auth_type")
                if isinstance(auth_type_val, str):
                    auth_type_val = AuthType(auth_type_val)
                elif auth_type_val is None:
                    auth_type_val = AuthType.NO_AUTH

                # Get required config values with defaults
                agent_url = str(worker_config.get("agent_url", ""))
                judge_model = str(worker_config.get("judge_llm", "openai/gpt-4o-mini"))
                auth_credentials = worker_config.get("auth_credentials")
                deep_test = bool(worker_config.get("deep_test_mode", False))

                # Create agent config
                agent_config = AgentConfig(
                    agent_url=HttpUrl(agent_url),
                    auth_type=auth_type_val,
                    auth_credentials=auth_credentials,
                    judge_llm_model=judge_model,
                    deep_test_mode=deep_test,
                )

                # Create evaluation request
                request = EvaluationRequest(
                    agent_config=agent_config,
                    scenarios=scenarios,
                )

                logger.info(f"Worker {worker_id}: Starting evaluation")
                await update_queue.put(
                    (
                        worker_id,
                        "status",
                        f"Starting evaluation (batch size: {len(scenarios)})",
                    )
                )

                # Define chat callback
                def on_chat_update(chat_data):
                    """Handle real-time chat updates from SDK"""
                    logger.info(
                        f"Worker {worker_id}: Received chat update: {chat_data}",
                    )
                    # Use asyncio.create_task to schedule the async operation
                    asyncio.create_task(
                        update_queue.put(
                            (
                                worker_id,
                                "chat",
                                {
                                    "role": chat_data.get("role", "assistant"),
                                    "content": chat_data.get("content", ""),
                                },
                            )
                        )
                    )

                # Define status callback
                def on_status_update(status_data):
                    """Handle real-time status updates from SDK"""
                    # status_data is now a dict, not an EvaluationJob object
                    status = status_data.get("status", "unknown")
                    progress = status_data.get("progress", 0.0)
                    error_msg = status_data.get("error_message")

                    logger.debug(f"Worker {worker_id}: Job status update: {status}")

                    if error_msg:
                        status_msg = f"Status: {status} - {error_msg}"
                    else:
                        status_msg = f"Status: {status} (progress: {progress:.1%})"

                    # Use asyncio.create_task to schedule the async operation
                    asyncio.create_task(
                        update_queue.put((worker_id, "status", status_msg))
                    )

                # Run evaluation with real-time updates
                try:
                    final_job = await sdk.run_evaluation_with_updates(
                        request=request,
                        on_update=on_status_update,
                        on_chat=on_chat_update,
                        timeout=600.0,
                    )

                    if final_job is None:
                        # Handle case where final job retrieval failed
                        logger.error(
                            f"Worker {worker_id}: Failed to get final job results",
                        )
                        await update_queue.put(
                            (
                                worker_id,
                                "chat",
                                {
                                    "role": "assistant",
                                    "content": (
                                        "❌ Evaluation failed for worker "
                                        f"{worker_id + 1}: Could not retrieve "
                                        "final results"
                                    ),
                                },
                            )
                        )
                        await update_queue.put(
                            (worker_id, "status", "Failed: Could not retrieve results")
                        )
                        await update_queue.put((worker_id, "done", None))
                        return

                    logger.info(
                        (
                            f"Worker {worker_id}: Evaluation completed with "
                            f"status: {final_job.status}",
                        )
                    )

                    if final_job.status == "completed" and final_job.results:
                        await update_queue.put(
                            (
                                worker_id,
                                "chat",
                                {
                                    "role": "assistant",
                                    "content": (
                                        "✅ Evaluation completed for worker "
                                        f"{worker_id + 1}!"
                                    ),
                                },
                            )
                        )
                        # Wrap the list of results in EvaluationResults
                        results = EvaluationResults(results=final_job.results or [])
                        await update_queue.put((worker_id, "done", results))
                    elif final_job.status == "failed":
                        error_msg = final_job.error_message or "Unknown error"
                        await update_queue.put(
                            (
                                worker_id,
                                "chat",
                                {
                                    "role": "assistant",
                                    "content": (
                                        "❌ Evaluation failed for worker "
                                        f"{worker_id + 1}: {error_msg}"
                                    ),
                                },
                            )
                        )
                        await update_queue.put(
                            (worker_id, "status", f"Failed: {error_msg}")
                        )
                        await update_queue.put((worker_id, "done", None))
                    else:
                        await update_queue.put(
                            (worker_id, "status", f"Evaluation {final_job.status}")
                        )
                        await update_queue.put((worker_id, "done", None))

                except Exception as eval_error:
                    logger.exception(f"evaluation failed for worker {worker_id}")
                    error_msg = str(eval_error)

                    # Provide user-friendly error messages
                    if "validation error" in error_msg.lower():
                        user_error = (
                            "Configuration error: Please check your evaluation settings"
                        )
                    elif "connection" in error_msg.lower():
                        user_error = (
                            "Connection error: Cannot reach the evaluation "
                            "server or agent"
                        )
                    elif "timeout" in error_msg.lower():
                        user_error = "Timeout error: Evaluation took too long"
                    else:
                        user_error = f"Evaluation error: {error_msg}"

                    await update_queue.put(
                        (
                            worker_id,
                            "chat",
                            {
                                "role": "assistant",
                                "content": (
                                    "❌ Worker " f"{worker_id + 1} failed: {user_error}"
                                ),
                            },
                        )
                    )
                    await update_queue.put(
                        (worker_id, "status", f"Error: {user_error}")
                    )
                    await update_queue.put((worker_id, "done", None))

            finally:
                await sdk.close()

        # Create and start worker tasks
        logger.info(f"🚀 Creating {len(scenario_batches)} worker tasks")
        worker_tasks = []
        for i, batch in enumerate(scenario_batches):
            logger.debug(f"Creating task for worker {i} with batch size {len(batch)}")
            task = asyncio.create_task(worker(batch, i))
            worker_tasks.append(task)
        logger.info(f"All {len(worker_tasks)} worker tasks created and started")

        # 4. --- Process Updates from Queue ---
        logger.info(f"📥 Starting update processing loop for {num_runners} workers")
        finished_workers = 0
        all_results = EvaluationResults()
        worker_histories = [[] for _ in range(num_runners)]

        while finished_workers < num_runners:
            logger.debug(
                (
                    "Waiting for update from queue... "
                    f"({finished_workers}/{num_runners} finished)"
                )
            )
            worker_id, update_type, data = await update_queue.get()
            logger.info(
                (
                    f"📨 Received update: worker_id={worker_id}, "
                    f"type={update_type}, data_preview={str(data)[:100]}"
                )
            )

            updates = get_blank_updates()
            if update_type == "status":
                logger.info(f"📊 Status update for worker {worker_id}: {data}")
                updates[worker_id * 3 + 1] = gr.update(value=data)
                logger.debug(
                    f"Status update prepared for component index {worker_id * 3 + 1}"
                )
            elif update_type == "chat":
                role = "user" if data["role"] == "Evaluator Agent" else "assistant"
                chat_message = {"role": role, "content": data["content"]}
                worker_histories[worker_id].append(chat_message)
                logger.info(
                    (
                        f"💬 Adding chat message for worker {worker_id}: "
                        f"role={role}, content={data['content'][:50]}..."
                    )
                )
                logger.debug(
                    (
                        f"Worker {worker_id} chat history now has "
                        f"{len(worker_histories[worker_id])} messages"
                    )
                )
                updates[worker_id * 3 + 2] = gr.update(
                    value=worker_histories[worker_id]
                )
                logger.debug(
                    f"Chat update prepared for component index {worker_id * 3 + 2}"
                )
            elif update_type == "done":
                finished_workers += 1
                logger.info(
                    f"✅ Worker {worker_id} finished ({finished_workers}/{num_runners})"
                )
                if data:
                    all_results.combine(data)
                    logger.debug(f"Combined results from worker {worker_id}")
                updates[worker_id * 3 + 1] = gr.update(
                    value="Finished.", interactive=False
                )

            logger.debug(f"Yielding {len(updates)} updates to UI")
            yield tuple(updates)

        # 5. --- Finalize and Summarize ---
        logger.info("All evaluation runs completed.")
        # workdir = state.get("workdir")

        # final_output_path = (
        #     workdir / f"evaluation_results_{datetime.now().isoformat()}.json"
        # )
        # final_output_path.write_text(all_results.model_dump_json(indent=2))

        # Generate summary using SDK (server-based)
        try:
            sdk_config = RogueClientConfig(
                base_url="http://localhost:8000",
                timeout=600.0,
            )
            sdk = RogueSDK(sdk_config)

            summary = await sdk.generate_summary(
                results=all_results,
                model=config.get("service_llm"),
                api_key=config.get("judge_llm_api_key"),
            )

            await sdk.close()
        except Exception as e:
            logger.warning(
                f"SDK summary generation failed, falling back to legacy: {e}"
            )
            # Fallback to legacy LLMService
            summary = LLMService().generate_summary_from_results(
                model=config.get("service_llm"),
                results=all_results,
                llm_provider_api_key=config.get("judge_llm_api_key"),
            )

        state["results"] = all_results
        state["summary"] = summary
        # state["evaluation_results_output_path"] = final_output_path

        final_ui_update = get_blank_updates()
        final_ui_update[-1] = gr.update(selected="report")
        yield tuple(final_ui_update)

    # Add logging to the main function instead
    original_run_and_evaluate = run_and_evaluate_scenarios

    async def logged_run_and_evaluate_scenarios(state):
        logger.info("🔴 Run button clicked!")
        logger.debug(
            f"Button click state keys: {list(state.keys()) if state else 'None'}"
        )
        async for update in original_run_and_evaluate(state):
            yield update

    run_button.click(
        fn=logged_run_and_evaluate_scenarios,
        inputs=[shared_state],
        outputs=output_components + [tabs_component],
    )

    return scenarios_display, run_button
