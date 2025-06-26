from typing import List

import gradio as gr

from ...services.llm_service import LLMService


def create_interviewer_screen(
    shared_state: gr.State,
    tabs_component: gr.Tabs,
):
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

            system_prompt = """
You are a business context interviewer whose job is to understand AI agent use cases for testing
purposes. Your goal is to gather information about a business's AI agent implementation so that
comprehensive test scenarios can be created using Rogue - a testing framework that evaluates AI
agent performance, compliance, and reliability.

Your primary focus should be on understanding business risks and critical scenarios, particularly
around:
- Financial risks (refunds, discounts, pricing, billing)
- Compliance requirements
- Customer service escalations
- Data handling and privacy
- Authorization and access controls
- Transaction processing
- Policy enforcement

Here are the key rules for your interview process:

1. Ask up to 5 questions maximum, one question at a time
2. Wait for the user's response before asking your next question
3. Focus each question on understanding specific business risks or critical scenarios
4. Tailor follow-up questions based on previous responses
5. After you have enough information (or after 5 questions), provide a comprehensive summary

Start by asking about the basic business use case and the AI agent's primary function. Then drill
down into specific risk areas based on their responses.

When you have gathered sufficient information, provide a summary that includes:
- Business domain and AI agent purpose
- Key business risks identified
- Critical scenarios that should be tested
- Compliance or regulatory considerations
- Potential failure modes or edge cases

Begin the interview now 

Format your questions clearly and keep them focused on one topic at a time. When ready to summarize,
put your final business context summary.

"""
            messages = [{"role": "system", "content": system_prompt}]
            for user_msg, assistant_msg in history:
                if user_msg:
                    messages.append({"role": "user", "content": user_msg})
                if assistant_msg:
                    messages.append({"role": "assistant", "content": assistant_msg})

            config = state.get("config", {})
            service_llm = config.get("service_llm", "openai/gpt-4.1")
            api_key = config.get("judge_llm_api_key")

            bot_message = llm_service.get_interview_question(
                model=service_llm,
                messages=messages,
                llm_provider_api_key=api_key,
            )

            # Add bot response to the last entry in history
            history[-1][1] = bot_message
            return "", history

        def finalize_context(state, history: List[List[str]]):
            if history and len(history) > 1 and history[-1][1] is not None:
                context = history[-1][1]
                state["business_context"] = context
                ("Business context finalized!")
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
