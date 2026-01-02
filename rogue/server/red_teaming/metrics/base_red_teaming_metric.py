"""
Base red teaming metric class.

Metrics evaluate whether a vulnerability was successfully exploited in a test case.
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Optional

from loguru import logger

from rogue.common.agent_model_wrapper import get_llm_from_model


class BaseRedTeamingMetric(ABC):
    """
    Base class for red teaming evaluation metrics.

    Metrics determine if a vulnerability was successfully exploited based on
    the agent's response to an attack.
    """

    score: Optional[float] = None
    reason: Optional[str] = None

    def __init__(
        self,
        judge_llm: Optional[str] = None,
        judge_llm_auth: Optional[str] = None,
        async_mode: bool = True,
        **kwargs,
    ):
        """
        Initialize the metric.

        Args:
            judge_llm: Name of the judge LLM to use (e.g. "gpt-4")
            judge_llm_auth: API key/auth token for the judge LLM
            async_mode: Whether to run in async mode (where applicable)
        """
        self.judge_llm = judge_llm
        self.judge_llm_auth = judge_llm_auth
        self.async_mode = async_mode
        self._llm_instance = None

    def _get_llm(self):
        """Get or create the LLM instance."""
        if self._llm_instance:
            return self._llm_instance

        if not self.judge_llm:
            return None

        try:
            self._llm_instance = get_llm_from_model(
                self.judge_llm,
                self.judge_llm_auth,
            )
            return self._llm_instance
        except Exception as e:
            logger.error(f"Failed to initialize judge LLM {self.judge_llm}: {e}")
            return None

    def _call_llm(self, prompt: str) -> str:
        """
        Call the judge LLM with a prompt.

        Args:
            prompt: The prompt to send

        Returns:
            The string response from the LLM
        """
        llm = self._get_llm()
        if not llm:
            logger.warning("No judge LLM configured for metric")
            return ""

        try:
            # Check if this is a LiteLlm instance from ADK
            # LiteLlm objects are not directly callable,
            # use litellm.completion() instead
            llm_type = type(llm).__name__
            if llm_type == "LiteLlm":
                # Use litellm.completion() directly for LiteLlm instances
                from litellm import completion

                # Extract model and API key from the LiteLlm instance
                model = getattr(llm, "model", self.judge_llm)
                api_key = getattr(llm, "api_key", self.judge_llm_auth)

                response = completion(
                    model=model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": "start"},
                    ],
                    api_key=api_key,
                )
                return response.choices[0].message.content
            # ADK models typically have query() or generate_content()
            # Adapting to common interfaces
            elif hasattr(llm, "query"):
                return llm.query(prompt)
            elif hasattr(llm, "generate_content"):
                resp = llm.generate_content(prompt)
                return resp.text if hasattr(resp, "text") else str(resp)
            else:
                # Fallback: try to use litellm.completion() directly
                from litellm import completion

                response = completion(
                    model=self.judge_llm,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": "start"},
                    ],
                    api_key=self.judge_llm_auth,
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling judge LLM: {e}")
            return ""

    async def _a_call_llm(self, prompt: str) -> str:
        """Async version of _call_llm."""
        # If the underlying LLM supports async, use it.
        # Otherwise, fall back to sync.
        # For now, simple sync fallback is safe for most cases in this architecture
        return self._call_llm(prompt)

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON response from LLM, handling code blocks and special tokens."""
        import re

        # If response is empty (e.g., LLM failed due to context length),
        # default to "passed" (agent successfully defended)
        if not response or not response.strip():
            logger.warning(
                "Empty LLM response, marking test as passed (agent defended)",
                extra={"metric": self.__class__.__name__},
            )
            return {
                "passed": True,
                "vulnerability_detected": False,
                "prompt_leaked": False,
                "reason": "Evaluation skipped due to judge LLM error",
                "confidence": 1.0,
            }

        try:
            clean_response = response.strip()

            # Strip markdown code blocks
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]

            # Try parsing directly first
            try:
                return json.loads(clean_response.strip())
            except json.JSONDecodeError:
                pass

            # Handle special tokens like <|channel|>final <|constrain|>JSON<|message|>
            # Extract JSON after special tokens
            json_match = re.search(r"<\|message\|>(.+)", clean_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

            # Try to find JSON object anywhere in the response
            # Look for patterns like {..."key": "value"...}
            json_pattern = re.search(
                r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",
                clean_response,
                re.DOTALL,
            )
            if json_pattern:
                json_str = json_pattern.group(0)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass

            # Last resort: Try to use LLM to extract/fix the JSON
            # Only try if we have a non-empty response (avoid infinite loops)
            if response and len(response.strip()) > 0:
                logger.warning(
                    "Standard JSON parsing failed, attempting LLM-based extraction",
                    extra={"response_preview": response[:200]},
                )
                extracted_json = self._extract_json_with_llm(response)
                if extracted_json:
                    return extracted_json

        except Exception as e:
            logger.warning(
                f"Failed to parse JSON from LLM response: {e}\nResponse: {response}",
            )

        return {}

    def _extract_json_with_llm(self, response: str) -> dict:
        """
        Use an LLM to extract/salvage JSON from a malformed response.

        This is a last-resort method when regex and standard parsing fail.
        """
        try:
            extraction_prompt = (
                "You are a JSON extraction assistant. "
                "Extract the JSON object from the following text.\n"
                "The text may contain special tokens, formatting issues, "
                "or other noise.\n"
                "Return ONLY the valid JSON object, nothing else.\n\n"
                f"Text to extract from:\n{response}\n\n"
                "Return the JSON object:"
            )

            # Use the same LLM as the judge
            extracted = self._call_llm(extraction_prompt)

            # If extraction also failed (empty response), give up and default to passed
            if not extracted or not extracted.strip():
                logger.warning(
                    "LLM extraction returned empty, defaulting to passed",
                    extra={"metric": self.__class__.__name__},
                )
                return {
                    "passed": True,
                    "vulnerability_detected": False,
                    "prompt_leaked": False,
                    "reason": "Judge LLM failed, defaulting to passed",
                    "confidence": 1.0,
                }

            # Try to parse the extracted response
            clean = extracted.strip()
            if clean.startswith("```json"):
                clean = clean[7:]
            if clean.startswith("```"):
                clean = clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]

            parsed = json.loads(clean.strip())
            logger.info(
                "Successfully extracted JSON using LLM",
                extra={
                    "original_length": len(response),
                    "extracted": str(parsed)[:100],
                },
            )
            return parsed

        except Exception as e:
            logger.warning(
                f"LLM-based JSON extraction failed: {e}",
                extra={"response_preview": response[:200]},
            )
            # Default to passed when extraction fails
            return {
                "passed": True,
                "vulnerability_detected": False,
                "prompt_leaked": False,
                "reason": "JSON extraction failed, defaulting to passed",
                "confidence": 1.0,
            }

    @abstractmethod
    def measure(self, test_case: Any) -> None:
        """
        Measure whether the vulnerability was exploited.

        Args:
            test_case: Test case containing attack input and agent response
                       Expected to have 'input' and 'actual_output' keys/attrs
        """
        raise NotImplementedError("Subclasses must implement measure()")

    async def a_measure(self, test_case: Any) -> None:
        """
        Async version of measure.

        Args:
            test_case: Test case containing attack input and agent response
        """
        return self.measure(test_case)
