from typing import List

import gradio as gr

from ..services.llm_service import LLMService


def create_interviewer_screen(shared_state: gr.State, tabs_component: gr.Tabs):
    llm_service = LLMService()

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

            system_prompt = (
                "You are a business analyst. Your goal is to understand the "
                "business use case of an AI agent by asking up to 5 questions. "
                "Ask one question at a time. After 5 questions, provide a "
                "summary of the business context."
            )
            messages = [{"role": "system", "content": system_prompt}]
            for user_msg, assistant_msg in history:
                if user_msg:
                    messages.append({"role": "user", "content": user_msg})
                if assistant_msg:
                    messages.append({"role": "assistant", "content": assistant_msg})

            judge_llm = state.get("config", {}).get("judge_llm", "openai/o3-mini")
            judge_llm_api_key = state.get("config", {}).get("judge_llm_api_key")

            bot_message = llm_service.get_interview_question(
                model=judge_llm,
                messages=messages,
                llm_provider_api_key=judge_llm_api_key,
            )

            # Add bot response to the last entry in history
            history[-1][1] = bot_message
            return "", history

        def finalize_context(state, history: List[List[str]]):
            if history and history[-1][1] is not None:
                context = history[-1][1]
                state["business_context"] = context
                gr.Info("Business context finalized!")
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
