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

        chatbot = gr.Chatbot(height=400, label="Interviewer")
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
            bot_message = llm_service.get_interview_question(
                model=judge_llm, messages=messages
            )

            # Add bot response to the last entry in history
            history[-1][1] = bot_message
            return "", history

        def finalize_context(state, history):
            if not history:
                gr.Warning("Cannot finalize an empty conversation.")
                return state, gr.update()

            # Build the message history for the summarization call
            messages = []
            for user_msg, assistant_msg in history:
                if user_msg:
                    messages.append({"role": "user", "content": user_msg})
                if assistant_msg:
                    # Don't include the initial welcome message in the summary context
                    if "Welcome!" in assistant_msg:
                        continue
                    messages.append({"role": "assistant", "content": assistant_msg})

            if not messages:
                gr.Warning("No valid conversation history to summarize.")
                return state, gr.update()

            judge_llm = state.get("config", {}).get("judge_llm", "openai/o3-mini")

            # Use the new summarization service
            summary = llm_service.summarize_business_context(
                model=judge_llm, messages=messages
            )

            state["business_context"] = summary
            gr.Info("Business context finalized!")
            return state, gr.Tabs(selected="scenarios")

        chatbot.value = [
            [
                None,
                "Welcome! I'll ask a few questions to understand your agent. What is the primary business domain your agent operates in?",
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
