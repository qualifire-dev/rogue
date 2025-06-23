import json
import os
from pathlib import Path

import gradio as gr
from loguru import logger
from pydantic import ValidationError

from ...models.config import AgentConfig, AuthType


def load_config_from_file(workdir: Path) -> dict:
    config_path = Path(workdir) / "user_config.json"

    # --- Pre-load keys from environment variables ---
    hf_key_env = os.environ.get("HUGGING_FACE_API_KEY") or os.environ.get("HF_TOKEN")

    if not config_path.exists():
        # Create an empty config file if it doesn't exist, then return empty config
        with open(config_path, "w") as f:
            json.dump({}, f)
        return {
            "huggingface_api_key": hf_key_env,
        }

    # If the file exists, try to load it
    with open(config_path, "r") as f:
        logger.info(f"Loading config from {config_path}")
        try:
            res = json.load(f)
            res["huggingface_api_key"] = hf_key_env
            logger.info(f"Loaded config: {res}")
            return res
        except json.JSONDecodeError:
            # If the file is empty or malformed, return an empty config
            return {}


def create_config_screen(
    shared_state: gr.State,
    tabs_component: gr.Tabs,
):
    with gr.Column():
        gr.Markdown("## Agent Configuration")
        agent_url = gr.Textbox(
            label="Agent URL",
            placeholder="http://localhost:8000/agent",
            value=shared_state.value.get(
                "config",
                {},
            ).get(
                "agent_url",
                "http://localhost:10001",
            ),
        )
        agent_url_error = gr.Markdown(visible=False, elem_classes=["error-label"])

        gr.Markdown("**Interview Mode**")
        interview_mode = gr.Checkbox(
            label="Enable AI-powered business context interview",
            value=shared_state.value.get(
                "config",
                {},
            ).get(
                "interview_mode",
                True,
            ),
        )
        gr.Markdown(
            "When enabled, you'll be guided through an AI-powered interview to "
            "extract your agent's business context. Turn off to skip this step."
        )

        auth_type = gr.Dropdown(
            label="Authentication Type",
            choices=[e.value for e in AuthType],
            value=shared_state.value.get(
                "config",
                {},
            ).get(
                "auth_type",
                AuthType.NO_AUTH.value,
            ),
        )
        auth_credentials = gr.Textbox(
            label="Authentication Credentials",
            type="password",
            visible=(
                shared_state.value.get(
                    "config",
                    {},
                ).get("auth_type", AuthType.NO_AUTH.value)
                != AuthType.NO_AUTH.value
            ),
        )
        auth_credentials_error = gr.Markdown(
            visible=False, elem_classes=["error-label"]
        )

        gr.Markdown("## Evaluator Configuration")
        gr.Markdown(
            "Specify the models to be used for the evaluation process. The **Interviewer LLM** is "
            "used to conduct the initial interview and generate test scenarios. The **Judge LLM** "
            "is used by the evaluator agent to score the agent's performance against those scenarios."
        )
        interviewer_llm = gr.Textbox(
            label="Interviewer LLM",
            value=shared_state.value.get(
                "config",
                {},
            ).get(
                "interviewer_llm",
                "openai/gpt-4.1",
            ),
        )
        judge_llm = gr.Textbox(
            label="Judge LLM",
            value=shared_state.value.get(
                "config",
                {},
            ).get(
                "judge_llm",
                "openai/gpt-4.1",
            ),
        )
        judge_llm_api_key = gr.Textbox(
            label="Judge LLM API Key",
            type="password",
            value=shared_state.value.get(
                "config",
                {},
            ).get("judge_llm_api_key", ""),
        )
        judge_llm_api_key_error = gr.Markdown(
            visible=False,
            elem_classes=["error-label"],
        )

        huggingface_api_key = gr.Textbox(
            label="HuggingFace API Key",
            type="password",
            value=shared_state.value.get(
                "config",
                {},
            ).get(
                "huggingface_api_key",
                "",
            ),
        )
        huggingface_api_key_error = gr.Markdown(
            visible=False, elem_classes=["error-label"]
        )

        save_button = gr.Button("Save Configuration")
        general_error_label = gr.Markdown(visible=False, elem_classes=["error-label"])

        error_labels = {
            "agent_url": agent_url_error,
            "auth_credentials": auth_credentials_error,
            "judge_llm_api_key": judge_llm_api_key_error,
            "huggingface_api_key": huggingface_api_key_error,
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
        (interviewer_llm, "interviewer_llm"),
        (judge_llm, "judge_llm"),
        (judge_llm_api_key, "judge_llm_api_key"),
        (huggingface_api_key, "huggingface_api_key"),
    ]:
        component.change(
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

    def save_config_to_file(config: dict, workdir: Path):
        config_path = Path(workdir) / "user_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

    def save_config(
        state,
        url,
        interview_mode_val,
        auth_t,
        creds,
        interviewer_llm_val,
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
                interviewer_llm=interviewer_llm_val,
                judge_llm=llm,
                judge_llm_api_key=llm_key,
                huggingface_api_key=hf_key,
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
                save_config_to_file(sanitized_config, workdir)

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
            auth_type,
            auth_credentials,
            interviewer_llm,
            judge_llm,
            judge_llm_api_key,
            huggingface_api_key,
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
        interviewer_llm,
        judge_llm,
        judge_llm_api_key,
        huggingface_api_key,
    )
