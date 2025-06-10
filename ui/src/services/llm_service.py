from typing import Optional

from litellm import completion
from pydantic import SecretStr


class LLMService:
    @staticmethod
    def get_interview_question(
        model: str,
        messages: list,
        llm_provider_api_key: Optional[SecretStr] = None,
    ) -> str:
        # Count user messages to decide if we should add the summary prompt.
        num_user_messages = sum(1 for msg in messages if msg["role"] == "user")

        if num_user_messages >= 5:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "You have asked 5 questions. Now, provide a "
                        "concise summary of the agent's business "
                        "context based on the conversation."
                    ),
                }
            )

        api_key = (
            None
            if llm_provider_api_key is None
            else llm_provider_api_key.get_secret_value()
        )

        try:
            response = completion(
                model=model,
                messages=messages,
                api_key=api_key,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"An error occurred: {e}"

    @staticmethod
    def generate_scenarios(
        model: str,
        context: str,
        llm_provider_api_key: Optional[SecretStr] = None,
    ) -> str:
        system_prompt = (
            "You are a test scenario designer. Based on the provided business "
            "context, generate 5 to 10 diverse test scenarios. The output "
            "must be a valid JSON array of objects, where each object "
            "conforms to the TestScenario Pydantic model structure. "
            "Include functional tests, edge cases, and error handling."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ]

        api_key = (
            None
            if llm_provider_api_key is None
            else llm_provider_api_key.get_secret_value()
        )

        try:
            response = completion(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                api_key=api_key,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f'{{"error": "Failed to generate scenarios: {e}"}}'
