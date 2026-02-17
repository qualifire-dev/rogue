"""OpenAI API Evaluator Agent.

Communicates with evaluated agents using the OpenAI chat completions API
via litellm for provider flexibility.
"""

from types import TracebackType
from typing import Callable, Optional, Self, Type

from loguru import logger
from rogue_sdk.types import Protocol, Scenarios, Transport

from ..base_evaluator_agent import BaseEvaluatorAgent


class OpenAIAPIEvaluatorAgent(BaseEvaluatorAgent):
    """Evaluator agent that uses OpenAI chat completions API via litellm."""

    def __init__(
        self,
        transport: Optional[Transport],
        evaluated_agent_address: str,
        judge_llm: str,
        scenarios: Scenarios,
        business_context: Optional[str],
        headers: Optional[dict[str, str]] = None,
        judge_llm_auth: Optional[str] = None,
        debug: bool = False,
        deep_test_mode: bool = False,
        chat_update_callback: Optional[Callable[[dict], None]] = None,
        *args,
        **kwargs,
    ):
        super().__init__(
            evaluated_agent_address=evaluated_agent_address,
            protocol=Protocol.OPENAI_API,
            transport=transport,
            judge_llm=judge_llm,
            scenarios=scenarios,
            business_context=business_context,
            headers=headers,
            judge_llm_auth=judge_llm_auth,
            debug=debug,
            deep_test_mode=deep_test_mode,
            chat_update_callback=chat_update_callback,
        )

    async def __aenter__(self) -> Self:
        return await super().__aenter__()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await super().__aexit__(exc_type, exc_value, traceback)

    async def _send_message_to_evaluated_agent(
        self,
        context_id: str,
        message: str,
    ) -> dict[str, str]:
        """
        Sends a message to the evaluated agent using OpenAI chat completions API.

        :param context_id: The context ID of the conversation.
            Each conversation has a unique context_id. All messages in the conversation
            have the same context_id.
        :param message: the text to send to the other agent.
        :return: A dictionary containing the response from the evaluated agent.
            - "response": the response string. If there is no response
                from the other agent, the string is empty.
        """
        logger.info(
            "🔗 Making OpenAI API call to evaluated agent",
            extra={
                "message": message[:100] + "..." if len(message) > 100 else message,
                "context_id": context_id,
                "agent_url": self._evaluated_agent_address,
                "transport": self._transport.value,
            },
        )

        self._add_message_to_chat_history(context_id, "user", message)
        response = await self._invoke_openai_api_agent(context_id, message)

        if not response or not response.get("response"):
            logger.debug(
                "_send_message_to_evaluated_agent - no response",
                extra={"protocol": "openai_api"},
            )
            return {"response": ""}

        self._add_message_to_chat_history(
            context_id,
            "assistant",
            response.get("response", "Not a text response"),
        )

        return response

    async def _invoke_openai_api_agent(
        self,
        context_id: str,
        message: str,
    ) -> dict[str, str]:
        """
        Invokes the evaluated agent using litellm's completion API.

        :param context_id: The context ID for the conversation.
        :param message: The message to send.
        :return: A dictionary with the response.
        """
        try:
            # litellm import takes a while, importing here to reduce startup time.
            from litellm import acompletion

            # Convert ChatHistory to OpenAI message format
            messages = []
            if context_id in self._context_id_to_chat_history:
                chat_history = self._context_id_to_chat_history[context_id]
                for msg in chat_history.messages:
                    messages.append({"role": msg.role, "content": msg.content})

            # Call the evaluated agent via litellm
            response = await acompletion(
                model="openai/evaluated-agent",  # Default model, can be overridden
                messages=messages,
                api_base=self._evaluated_agent_address,
                extra_headers=self._headers,
                timeout=30.0,
            )

            # Extract the assistant's response
            assistant_message = response.choices[0].message.content or ""

            logger.info(
                "✅ OpenAI API call successful - received response from evaluated agent",
                extra={
                    "response_length": len(assistant_message),
                    "response_preview": (
                        assistant_message[:100] + "..."
                        if len(assistant_message) > 100
                        else assistant_message
                    ),
                    "context_id": context_id,
                },
            )

            return {"response": assistant_message}

        except Exception as e:
            logger.exception(
                "❌ OpenAI API call failed - error sending message to evaluated agent",
                extra={
                    "protocol": "openai_api",
                    "agent_url": self._evaluated_agent_address,
                    "transport": self._transport.value,
                    "message": message[:100] + "..." if len(message) > 100 else message,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return {
                "response": "",
                "error": str(e),
            }
