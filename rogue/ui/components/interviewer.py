from typing import List

import gradio as gr

from ...common.workdir_utils import dump_business_context
from ...services.interviewer_service import InterviewerService


def create_interviewer_screen(
    shared_state: gr.State,
    tabs_component: gr.Tabs,
):
    with gr.Column():
        gr.Markdown("## AI-Powered Interviewer")
        gr.Markdown(
            "Answer up to 5 questions to help us understand your agent's "
            "business use case."
        )

        chatbot = gr.Chatbot(height=400, label="Interviewer", type="tuples")
        user_input = gr.Textbox(
            show_label=False,
            placeholder="Enter your response here...",
        )
        finalize_button = gr.Button("Finalize Business Context")

        def respond(message, history, state):
            # Append user message to history for display
            history.append([message, None])
            config = state.get("config", {})
            service_llm = config.get("service_llm", "openai/gpt-4.1")
            api_key = config.get("judge_llm_api_key")

            if "interviewer_service" not in state:
                state["interviewer_service"] = InterviewerService(
                    model=service_llm,
                    llm_provider_api_key=api_key,
                )
            interviewer_service = state["interviewer_service"]
            bot_message = interviewer_service.send_message(message)

            # Add bot response to the last entry in history
            history[-1][1] = bot_message
            return "", history

        def finalize_context(state, history: List[List[str]]):
            if history and len(history) > 1 and history[-1][1] is not None:
                context = history[-1][1]
                state["business_context"] = context
                dump_business_context(state, context)
                return state, gr.Tabs(selected="scenarios")

            gr.Warning("Could not determine business context from conversation.")
            return state, gr.update()

        chatbot.value = [
            [
                None,
                "Welcome! I'll ask a few questions to understand your agent. "
                "What is the primary business domain your agent operates in?",
            ]
        ]

        user_input.submit(
            fn=respond,
            inputs=[user_input, chatbot, shared_state],
            outputs=[user_input, chatbot],
        )

        finalize_button.click(
            fn=finalize_context,
            inputs=[shared_state, chatbot],
            outputs=[shared_state, tabs_component],
        )

    return [chatbot, user_input, finalize_button]
