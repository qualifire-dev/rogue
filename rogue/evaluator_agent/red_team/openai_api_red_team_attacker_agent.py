"""OpenAI API Red Team Attacker Agent - Attacks using OpenAI API protocol."""

from types import TracebackType
from typing import Optional, Self, Type

from loguru import logger

from .base_red_team_attacker_agent import BaseRedTeamAttackerAgent


class OpenAIAPIRedTeamAttackerAgent(BaseRedTeamAttackerAgent):
    """Red team attacker agent using OpenAI API protocol."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Context ID to messages mapping for multi-turn conversations
        self._context_id_to_messages: dict[str, list[dict[str, str]]] = {}

    async def __aenter__(self) -> Self:
        """Initialize agent."""
        await super().__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Clean up resources."""
        await super().__aexit__(exc_type, exc_value, traceback)

    async def _send_message_to_evaluated_agent(
        self,
        message: str,
        session_id: Optional[str],
    ) -> str:
        """Send attack message via OpenAI API protocol using litellm."""
        try:
            # litellm import takes a while, importing here to reduce startup time.
            from litellm import acompletion

            context_id = session_id or "default"

            logger.debug(
                f"Sending OpenAI API message to {self._evaluated_agent_address}",
                extra={"context_id": context_id, "message_preview": message[:100]},
            )

            # Initialize or get existing message history for this context
            if context_id not in self._context_id_to_messages:
                self._context_id_to_messages[context_id] = []

            # Add the new user message
            self._context_id_to_messages[context_id].append(
                {"role": "user", "content": message},
            )

            # Prepare headers
            headers = {}
            if self._auth_type and self._auth_credentials:
                auth_headers = self._auth_type.get_auth_header(self._auth_credentials)
                headers.update(auth_headers)

            # Call the evaluated agent via litellm
            response = await acompletion(
                model="openai/evaluated-agent",
                messages=self._context_id_to_messages[context_id],
                api_base=self._evaluated_agent_address,
                headers=headers,
                timeout=30.0,
            )

            # Extract the assistant's response
            assistant_message = response.choices[0].message.content or ""

            # Add assistant response to message history
            self._context_id_to_messages[context_id].append(
                {"role": "assistant", "content": assistant_message},
            )

            logger.debug(
                "Received response from agent",
                extra={
                    "has_response": bool(assistant_message),
                    "response_length": len(assistant_message),
                },
            )

            if not assistant_message:
                logger.warning("No response from agent")
                return "No response from agent"

            return assistant_message

        except Exception as e:
            logger.error(
                f"Failed to send OpenAI API message: {e}",
                extra={"agent_url": self._evaluated_agent_address},
            )
            return f"Error: {str(e)}"
