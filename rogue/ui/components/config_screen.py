import gradio as gr
from loguru import logger
from pydantic import ValidationError

from ...common.workdir_utils import dump_config
from ...models.config import AgentConfig, AuthType


def create_config_screen(
    shared_state: gr.State,
    tabs_component: gr.Tabs,
):
    config_data = {}
    if shared_state.value and isinstance(shared_state.value, dict):
        config_data = shared_state.value.get("config", {})

    with gr.Column():
        gr.Markdown("## Agent Configuration")
        agent_url = gr.Textbox(
            label="Agent URL",
            placeholder="http://localhost:8000",
            value=config_data.get(
                "agent_url",
                "http://localhost:10001",
            ),
        )
        agent_url_error = gr.Markdown(visible=False, elem_classes=["error-label"])

        gr.Markdown("**Interview Mode**")
        interview_mode = gr.Checkbox(
            label="Enable AI-powered business context interview",
            value=config_data.get(
                "interview_mode",
                True,
            ),
        )
        gr.Markdown(
            "When enabled, you'll be guided through an AI-powered interview to "
            "extract your agent's business context. Turn off to skip this step."
        )

        gr.Markdown("**Deep Test Mode**")
        deep_test_mode = gr.Checkbox(
            label="Enable deep test mode.",
            value=config_data.get("deep_test_mode", False),
        )
        gr.Markdown(
            "When enabled, the evaluator will "
            "approach each scenario from different angles"
        )

        gr.Markdown("### Parallel Runs")
        parallel_runs = gr.Slider(
            label="Number of parallel evaluation runs",
            minimum=1,
            maximum=10,
            step=1,
            value=config_data.get("parallel_runs", 1),
        )
        gr.Markdown("### Authentication")

        auth_type = gr.Dropdown(
            label="Authentication Type",
            choices=[e.value for e in AuthType],
            value=config_data.get(
                "auth_type",
                AuthType.NO_AUTH.value,
            ),
        )
        auth_credentials = gr.Textbox(
            label="Authentication Credentials",
            type="password",
            visible=(
                config_data.get("auth_type", AuthType.NO_AUTH.value)
                != AuthType.NO_AUTH.value
            ),
        )
        auth_credentials_error = gr.Markdown(
            visible=False, elem_classes=["error-label"]
        )

        gr.Markdown("## Evaluator Configuration")
        gr.Markdown(
            "Specify the models for the evaluation process. "
            "The **Service LLM** will be used to interview, "
            "generate scenarios and summaries. The **Judge LLM** is used by the "
            "evaluator agent to score the agent's performance against those scenarios."
        )
        gr.Markdown(
            "ℹ️ Under the hood we're using `litellm`. See the "
            "[list of supported models](https://docs.litellm.ai/docs/providers). "
            "You can use environment variables for API keys."
        )

        service_llm = gr.Textbox(
            label="Service LLM",
            value=config_data.get(
                "service_llm",
                "openai/gpt-4.1",
            ),
        )
        judge_llm = gr.Textbox(
            label="Judge LLM",
            value=config_data.get(
                "judge_llm",
                "openai/o4-mini",
            ),
        )
        judge_llm_api_key = gr.Textbox(
            label="Judge LLM API Key",
            type="password",
            value=config_data.get("judge_llm_api_key", ""),
        )
        judge_llm_api_key_error = gr.Markdown(
            visible=False,
            elem_classes=["error-label"],
        )

        # huggingface_api_key = gr.Textbox(
        #     label="HuggingFace API Key",
        #     type="password",
        #     value=config_data.get(
        #         "huggingface_api_key",
        #         "",
        #     ),
        # )
        # huggingface_api_key_error = gr.Markdown(
        #     visible=False, elem_classes=["error-label"]
        # )

        save_button = gr.Button("Save Configuration")
        general_error_label = gr.Markdown(visible=False, elem_classes=["error-label"])

        error_labels = {
            "agent_url": agent_url_error,
            "auth_credentials": auth_credentials_error,
            "judge_llm_api_key": judge_llm_api_key_error,
            # "huggingface_api_key": huggingface_api_key_error,
        }

    def update_state(state, key, value):
        logger.info(f"Updating state: {key} = {value}")
        state["config"][key] = value
        return state

    for component, key in [
        (agent_url, "agent_url"),
        (interview_mode, "interview_mode"),
        (auth_type, "auth_type"),
        (auth_credentials, "auth_credentials"),
        (service_llm, "service_llm"),
        (judge_llm, "judge_llm"),
        (judge_llm_api_key, "judge_llm_api_key"),
        # (huggingface_api_key, "huggingface_api_key"),
        (deep_test_mode, "deep_test_mode"),
        (parallel_runs, "parallel_runs"),
    ]:
        component.change(  # type: ignore
            fn=update_state,
            inputs=[shared_state, gr.State(key), component],
            outputs=[shared_state],
        )

    def toggle_auth_credentials(auth_t):
        is_visible = auth_t != AuthType.NO_AUTH.value
        return gr.update(visible=is_visible)

    auth_type.change(
        fn=toggle_auth_credentials,
        inputs=[auth_type],
        outputs=[auth_credentials],
    )

    def save_config(
        state,
        url,
        interview_mode_val,
        deep_test_mode_val,
        parallel_runs_val,
        auth_t,
        creds,
        service_llm_val,
        llm,
        llm_key,
        hf_key,
    ):
        # Start by creating updates to clear all error labels
        label_updates = {
            label: gr.update(value="", visible=False) for label in error_labels.values()
        }
        label_updates[general_error_label] = gr.update(value="", visible=False)

        try:
            config = AgentConfig(
                agent_url=url,
                auth_type=auth_t,
                auth_credentials=creds,
                service_llm=service_llm_val,
                judge_llm=llm,
                judge_llm_api_key=llm_key,
                huggingface_api_key=hf_key,
                deep_test_mode=deep_test_mode_val,
                parallel_runs=parallel_runs_val,
            )

            config_dict = config.model_dump(mode="json")
            config_dict["interview_mode"] = interview_mode_val
            state["config"] = config_dict

            sanitized_config = {
                k: v
                for k, v in config_dict.items()
                if not k.endswith("_key") and k != "auth_credentials"
            }

            # Save sanitized config to file
            workdir = state.get("workdir")
            if workdir:
                dump_config(state, sanitized_config)

            next_tab = "interview" if interview_mode_val else "scenarios"
            return {
                **label_updates,
                tabs_component: gr.update(selected=next_tab),
                shared_state: state,
            }
        except ValidationError as e:
            error_updates = {
                label: gr.update(value="", visible=False)
                for label in error_labels.values()
            }
            error_updates[general_error_label] = gr.update(value="", visible=False)

            for error in e.errors():
                loc = error["loc"][0]
                msg = error["msg"]
                if loc in error_labels:
                    error_updates[error_labels[loc]] = gr.update(
                        value=f"**Error:** {msg}", visible=True
                    )
                else:
                    logger.error(f"Unhandled validation error: {error}")
                    error_updates[general_error_label] = gr.update(
                        value=f"**An unexpected error occurred:** {msg}",
                        visible=True,
                    )

            # Important: return the state even on failure to not lose user input
            return {**error_updates, shared_state: state}

    save_button.click(
        fn=save_config,
        inputs=[
            shared_state,
            agent_url,
            interview_mode,
            deep_test_mode,
            parallel_runs,
            auth_type,
            auth_credentials,
            service_llm,
            judge_llm,
            judge_llm_api_key,
            # huggingface_api_key,
        ],
        outputs=[
            shared_state,
            tabs_component,
            general_error_label,
            *error_labels.values(),
        ],
    )

    return (
        agent_url,
        interview_mode,
        auth_type,
        auth_credentials,
        service_llm,
        judge_llm,
        judge_llm_api_key,
        # huggingface_api_key,
        deep_test_mode,
        parallel_runs,
    )
