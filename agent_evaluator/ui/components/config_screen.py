import gradio as gr
from pydantic import ValidationError

from ...models.config import AgentConfig, AuthType


def create_config_screen(shared_state: gr.State, tabs_component: gr.Tabs):
    with gr.Column():
        gr.Markdown("## Agent Configuration")
        agent_url = gr.Textbox(
            label="Agent URL",
            placeholder="http://localhost:8000/agent",
            value="http://localhost:10001",
        )
        agent_url_error = gr.Markdown(visible=False, elem_classes=["error-label"])

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
        judge_llm_api_key = gr.Textbox(label="Judge LLM API Key", type="password")
        judge_llm_api_key_error = gr.Markdown(
            visible=False, elem_classes=["error-label"]
        )

        huggingface_api_key = gr.Textbox(label="HuggingFace API Key", type="password")
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

    def save_config(state, url, auth_t, creds, llm, llm_key, hf_key):
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
            state["config"] = config.model_dump()
            gr.Info("Configuration saved!")

            outputs = [state, gr.Tabs(selected="interview")] + list(
                label_updates.values()
            )
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
        auth_type,
        auth_credentials,
        judge_llm,
        judge_llm_api_key,
        huggingface_api_key,
        save_button,
    ]
