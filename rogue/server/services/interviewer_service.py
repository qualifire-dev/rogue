from typing import Any, Dict, Iterator

from litellm import completion

INTERVIEWER_SYSTEM_PROMPT = """
You are an AI interviewer tasked with extracting a business context from a user about their AI agent.
Your goal is to gather enough information to later generate test scenarios,
including edge cases, happy and sad flows, and key business risks.
Follow these instructions carefully:


1. After each user response, analyze the information provided in the user's response.
   First understand the full flow of the product.
   Look for key details about the AI agent's functionality, use cases, and potential risks.

2. Ask follow-up question about the edge cases,
   focusing on areas that need clarification or expansion.
   Focus specifically on business risks, edge cases, and happy and sad flows.
   like refunds, discounts, broken flows, etc.
   Prioritize questions that will help identify:
   a. Edge cases
   b. Happy and sad flows
   c. Key business risks (e.g., unauthorized refunds or discounts)

3. Keep your questions concise and relevant.
   Avoid asking multiple questions at once or repeating information the
   user has already provided.

4. As you gather information, mentally note the following:
   a. The AI agent's primary function and industry
   b. Key features and capabilities
   c. User interactions and workflows
   d. Potential failure points or vulnerabilities
   e. Compliance requirements or regulatory considerations

5. When explicitly asked to provide a business context summary, provide ONLY the summary
   in a clean, structured format. Do NOT ask follow-up questions or prompt for changes.
   The summary should be a comprehensive standalone document.

Remember to be polite, professional, and efficient throughout the interview process.
Your goal is to extract the necessary information as quickly as possible while ensuring accuracy and completeness.

Begin the interview by introducing yourself and asking the first question about the AI agent's primary function.
"""  # noqa: E501


class InterviewerService:
    def __init__(
        self,
        model: str | None = None,
        llm_provider_api_key: str | None = None,
    ):
        self._model = model

        if llm_provider_api_key == "":
            llm_provider_api_key = None
        self._llm_provider_api_key = llm_provider_api_key

        self._messages = [
            {"role": "system", "content": INTERVIEWER_SYSTEM_PROMPT},
        ]

    def send_message(self, user_input: str):
        self._messages.append(
            {
                "role": "user",
                "content": user_input,
            },
        )

        # Copying the messages to avoid modifying the original list
        # in case we add the "stop" message
        messages = self._messages.copy()
        num_user_messages = sum(1 for msg in self._messages if msg["role"] == "user")

        if num_user_messages >= 3:  # add stop message
            # We don't want to save it to the self._messages list
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "You have asked 3 questions. Now, provide a concise "
                        "summary of the agent's business context based on the "
                        "conversation. Provide ONLY the business context summary "
                        "in a clean, structured format. Do NOT ask any follow-up "
                        "questions or prompt for changes. This should be a "
                        "standalone business context document."
                    ),
                },
            )

        try:
            response = completion(
                model=self._model,
                messages=messages,
                api_key=self._llm_provider_api_key,
            )

            self._messages.append(
                {
                    "role": "assistant",
                    "content": response.choices[0].message.content,
                },
            )
            return response.choices[0].message.content

        except Exception as e:
            return f"An error occurred: {e}"

    def count_user_messages(self) -> int:
        return sum(1 for msg in self._messages if msg["role"] == "user")

    def iter_messages(self, include_system: bool = False) -> Iterator[Dict[str, Any]]:
        return (
            msg for msg in self._messages if include_system or msg["role"] != "system"
        )
