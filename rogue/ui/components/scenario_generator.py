import asyncio
from typing import TYPE_CHECKING

from loguru import logger
from rogue_sdk import RogueClientConfig, RogueSDK

from ...common.workdir_utils import dump_business_context, dump_scenarios

if TYPE_CHECKING:
    from gradio import State, Tabs


def create_scenario_generator_screen(shared_state: "State", tabs_component: "Tabs"):
    # gradio import takes a while, importing here to reduce startup time.
    import gradio as gr

    with gr.Column():
        gr.Markdown("## Scenario Generation")
        business_context_display = gr.Textbox(
            label="Finalized Business Context",
            lines=5,
            interactive=True,
            placeholder="Please provide a brief summary of your agent's business "
            "context, including its main goals, user interactions, "
            "and key functionalities.",
        )
        scenarios_output = gr.JSON(label="Generated Scenarios")
        generate_button = gr.Button("Generate Scenarios")

    def generate_and_display_scenarios(state, current_context):
        if not current_context:
            gr.Warning("Business context is empty. Please finalize it first.")
            return state, None, gr.update()
        logger.info("Generating scenarios")

        # Update the shared state with the potentially edited context
        state["business_context"] = current_context
        dump_business_context(state, current_context)

        config = state.get("config", {})
        service_llm = config.get("service_llm")
        api_key = config.get("judge_llm_api_key")

        async def generate_scenarios_async():
            # Try SDK first (server-based)
            sdk_config = RogueClientConfig(
                base_url=state.get("rogue_server_url", "http://localhost:8000"),
                timeout=600.0,
            )
            sdk = RogueSDK(sdk_config)
            try:
                return await sdk.generate_scenarios(
                    business_context=current_context,
                    model=service_llm,
                    api_key=api_key,
                )
            except Exception:
                logger.exception("Failed to generate scenarios from LLM response.")
            finally:
                await sdk.close()

        try:
            scenarios = asyncio.run(generate_scenarios_async())
            dump_scenarios(state, scenarios)
            state["scenarios"] = scenarios

            return {
                shared_state: state,
                scenarios_output: scenarios.model_dump_json(
                    indent=2,
                    exclude_none=True,
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
