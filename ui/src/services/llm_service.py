from litellm import completion
from loguru import logger


class LLMService:
    def get_interview_question(self, model: str, messages: list) -> str:
        # Count user messages to decide if we should add the summary prompt.
        num_user_messages = sum(1 for msg in messages if msg["role"] == "user")

        if num_user_messages >= 5:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "You have asked 5 questions. Now, provide a "
                        "concise summary of the agent's business "
                        "context based on the conversation."
                    ),
                }
            )

        try:
            response = completion(model=model, messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            return f"An error occurred: {e}"

    def summarize_business_context(self, model: str, messages: list) -> str:
        system_prompt = (
            "You are a business analyst. Your task is to provide a concise "
            "summary of the agent's business context based on the provided "
            "conversation history. The summary should be a single, "
            "well-structured paragraph."
        )
        # Add the summarization instruction to the existing messages
        messages_with_prompt = messages + [{"role": "system", "content": system_prompt}]

        try:
            logger.info(f"Summarizing business context with model: {model}")
            response = completion(model=model, messages=messages_with_prompt)
            return response.choices[0].message.content
        except Exception as e:
            return f"An error occurred during summarization: {e}"

    def generate_scenarios(self, model: str, context: str) -> str:
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

        try:
            response = completion(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as e:
            return f'{{"error": "Failed to generate scenarios: {e}"}}'
