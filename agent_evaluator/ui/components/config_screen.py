import gradio as gr
from loguru import logger
from pydantic import ValidationError
import json
from pathlib import Path
import os

from ...models.config import AgentConfig, AuthType


def load_config_from_file(workdir: Path) -> dict:
    config_path = Path(workdir) / "user_config.json"
    logger.info(f"Config file not found at {config_path}, creating empty config")
    if not config_path.exists():
        # Create an empty config file if it doesn't exist, then return empty config
        with open(config_path, "w") as f:
            json.dump({}, f)
        return {}

    # If the file exists, try to load it
    with open(config_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # If the file is empty or malformed, return an empty config
            return {}


def create_config_screen(shared_state: gr.State, tabs_component: gr.Tabs):
    # --- Pre-load keys from environment variables ---
    judge_llm_key_env = (
        os.environ.get("OPENAI_API_KEY")
        or os.environ.get("ANTHROPIC_API_KEY")
        or os.environ.get("COHERE_API_KEY")
        or os.environ.get("REPLICATE_API_KEY")
        or os.environ.get("AZURE_API_KEY")
    )
    hf_key_env = os.environ.get("HUGGING_FACE_API_KEY") or os.environ.get("HF_TOKEN")

    with gr.Column():
        gr.Markdown("## Agent Configuration")
        agent_url = gr.Textbox(
            label="Agent URL",
            placeholder="http://localhost:8000/agent",
            value="http://localhost:10001",
        )
        agent_url_error = gr.Markdown(visible=False, elem_classes=["error-label"])

        # with gr.Group():
        gr.Markdown("**Interview Mode**")
        interview_mode = gr.Checkbox(
            label="Enable AI-powered business context interview",
            value=True,
        )
        gr.Markdown(
            "When enabled, you'll be guided through an AI-powered interview to extract your agent's business context. Turn off to skip this step."
        )

        auth_type = gr.Dropdown(
            label="Authentication Type",
            choices=[e.value for e in AuthType],
            value=AuthType.NO_AUTH.value,
        )
        auth_credentials = gr.Textbox(
            label="Authentication Credentials",
            type="password",
            visible=(AuthType.NO_AUTH.value != AuthType.NO_AUTH.value),
        )
        auth_credentials_error = gr.Markdown(
            visible=False, elem_classes=["error-label"]
        )

        gr.Markdown("## Evaluator Configuration")
        judge_llm = gr.Textbox(label="Judge LLM", value="openai/gpt-4.1-nano")
        judge_llm_api_key = gr.Textbox(
            label="Judge LLM API Key", type="password", value=judge_llm_key_env
        )
        judge_llm_api_key_error = gr.Markdown(
            visible=False, elem_classes=["error-label"]
        )

        huggingface_api_key = gr.Textbox(
            label="HuggingFace API Key", type="password", value=hf_key_env
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
        state, url, interview_mode_val, auth_t, creds, llm, llm_key, hf_key
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
                judge_llm=llm,
                judge_llm_api_key=llm_key,
                huggingface_api_key=hf_key,
            )
            config_dict = config.model_dump(mode="json")
            config_dict["interview_mode"] = interview_mode_val
            state["config"] = config_dict

            # Create a sanitized config for saving to file (no secrets)
            sanitized_config = {
                k: v
                for k, v in config_dict.items()
                if not k.endswith("_key") and k != "auth_credentials"
            }

            # Save sanitized config to file
            workdir = state.get("workdir")
            if workdir:
                save_config_to_file(sanitized_config, workdir)

            gr.Info("Configuration saved!")
            next_tab = "interview" if interview_mode_val else "scenarios"
            outputs = [state, gr.Tabs(selected=next_tab)] + list(label_updates.values())
            return outputs

        except ValidationError as e:
            for error in e.errors():
                loc = error.get("loc", ())
                # Check if it's a field-specific error we can handle
                if loc and loc[0] in error_labels:
                    field_name = loc[0]
                    msg = f"<p style='color:#D32F2F;'>{error['msg']}</p>"
                    label_updates[error_labels[field_name]] = gr.update(
                        value=msg, visible=True
                    )
                else:
                    # Otherwise, treat it as a general error
                    msg = f"<p style='color:#D32F2F;'>{error['msg']}</p>"
                    label_updates[general_error_label] = gr.update(
                        value=msg, visible=True
                    )

            outputs = [state, gr.update()] + list(label_updates.values())
            return outputs

        except Exception as e:
            error_html = (
                f"<p style='color:#D32F2F;'>An unexpected error occurred: {e}</p>"
            )
            label_updates[general_error_label] = gr.update(
                value=error_html, visible=True
            )
            outputs = [state, gr.update()] + list(label_updates.values())
            return outputs

    save_button.click(
        fn=save_config,
        inputs=[
            shared_state,
            agent_url,
            interview_mode,
            auth_type,
            auth_credentials,
            judge_llm,
            judge_llm_api_key,
            huggingface_api_key,
        ],
        outputs=(
            [shared_state, tabs_component]
            + list(error_labels.values())
            + [general_error_label]
        ),
    )

    # Note: The returned list of components for the screen itself
    # doesn't change Gradio's layout
    return [
        agent_url,
        interview_mode,
        auth_type,
        auth_credentials,
        judge_llm,
        judge_llm_api_key,
        huggingface_api_key,
        save_button,
    ]
