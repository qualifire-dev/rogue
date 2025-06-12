from litellm import completion


class EvaluationService:
    def evaluate_response(
        self,
        judge_llm_model: str,
        judge_llm_api_key: str,
        expected_output: dict,
        agent_response: dict,
    ) -> str:
        """
        Uses a user-configured LLM to evaluate the agent's response.
        """
        system_prompt = (
            "You are a test evaluator. Your task is to compare the agent's "
            "response to the expected output. Provide a score from 1 to 10, "
            "where 1 is a complete failure and 10 is a perfect match. "
            "Also, provide a brief justification for your score. "
            "The output must be a valid JSON object with two keys: "
            "'score' (int) and 'reasoning' (str)."
        )

        user_prompt = (
            f"Expected Output: {expected_output}\n\n"
            f"Agent Response: {agent_response}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = completion(
                model=judge_llm_model,
                messages=messages,
                api_key=judge_llm_api_key,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as e:
            return f'{{"score": 1, "reasoning": "Evaluation failed: {e}"}}'
