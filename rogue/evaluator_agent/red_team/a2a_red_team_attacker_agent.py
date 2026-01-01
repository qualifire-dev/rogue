"""A2A Red Team Attacker Agent - Attacks using A2A protocol."""

from typing import Optional
from uuid import uuid4

from a2a.client import A2ACardResolver
from a2a.types import Message, MessageSendParams, Part, Role, Task, TextPart
from httpx import AsyncClient
from loguru import logger

from ...common.remote_agent_connection import RemoteAgentConnections
from .base_red_team_attacker_agent import BaseRedTeamAttackerAgent


class A2ARedTeamAttackerAgent(BaseRedTeamAttackerAgent):
    """Red team attacker agent using A2A protocol."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._http_client: Optional[AsyncClient] = None
        self._agent_client: Optional[RemoteAgentConnections] = None

    async def __aenter__(self):
        """Initialize HTTP client and agent connection."""
        await super().__aenter__()
        self._http_client = AsyncClient(timeout=30)
        await self._http_client.__aenter__()

        # Initialize agent client
        card_resolver = A2ACardResolver(
            self._http_client,
            self._evaluated_agent_address,
        )
        card = await card_resolver.get_agent_card()
        self._agent_client = RemoteAgentConnections(
            self._http_client,
            card,
        )

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Clean up HTTP client."""
        if self._http_client:
            await self._http_client.__aexit__(exc_type, exc_value, traceback)
        await super().__aexit__(exc_type, exc_value, traceback)

    async def _send_message_to_evaluated_agent(
        self,
        message: str,
        session_id: Optional[str],
    ) -> str:
        """Send attack message via A2A protocol."""
        if not self._agent_client:
            raise RuntimeError("Agent client not initialized")

        try:
            context_id = session_id or uuid4().hex

            logger.debug(
                f"Sending A2A message to {self._evaluated_agent_address}",
                extra={"context_id": context_id, "message_preview": message[:100]},
            )

            # Force non-streaming mode to get Message responses instead of Task
            response = await self._agent_client.send_message(
                MessageSendParams(
                    message=Message(
                        contextId=context_id,
                        messageId=uuid4().hex,
                        role=Role.user,
                        parts=[
                            Part(
                                root=TextPart(
                                    text=message,
                                ),
                            ),
                        ],
                    ),
                ),
                stream=False,  # Force non-streaming to get Message response
            )

            logger.debug(
                "Received response from agent",
                extra={
                    "has_response": response is not None,
                    "response_type": type(response).__name__ if response else None,
                    "has_parts": hasattr(response, "parts") if response else False,
                },
            )

            if not response:
                logger.warning("No response from agent")
                return "No response from agent"

            # Handle different response types (Task or Message)
            response_text = ""

            # If response is a Task, extract from artifacts
            if isinstance(response, Task):
                logger.debug("Response is a Task, extracting from artifacts")
                if response.artifacts:
                    for artifact in response.artifacts:
                        if artifact.parts:
                            for part in artifact.parts:
                                if part.root and part.root.kind == "text":
                                    if part.root.text:
                                        response_text += str(part.root.text)

            # If response is a Message, extract from parts
            elif isinstance(response, Message):
                logger.debug("Response is a Message, extracting from parts")
                if response.parts:
                    for part in response.parts:
                        if part.root and part.root.kind == "text":
                            if part.root.text:
                                response_text += str(part.root.text)

            if not response_text:
                logger.warning(
                    "Could not extract text from response",
                    extra={
                        "response_type": type(response).__name__,
                        "is_task": isinstance(response, Task),
                        "is_message": isinstance(response, Message),
                        "has_parts": hasattr(response, "parts"),
                        "has_artifacts": hasattr(response, "artifacts"),
                    },
                )
                return "No text content in response"

            return response_text

        except Exception as e:
            logger.error(
                f"Failed to send A2A message: {e}",
                extra={"agent_url": self._evaluated_agent_address},
            )
            return f"Error: {str(e)}"
