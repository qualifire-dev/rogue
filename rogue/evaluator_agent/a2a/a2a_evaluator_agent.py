import json
from types import TracebackType
from typing import Callable, Optional, Self, Type
from uuid import uuid4

from a2a.client import A2ACardResolver
from a2a.types import Message, MessageSendParams, Part, Role, Task, TextPart
from httpx import AsyncClient
from loguru import logger
from rogue_sdk.types import Protocol, Scenarios, Transport

from ...common.remote_agent_connection import (
    JSON_RPC_ERROR_TYPES,
    RemoteAgentConnections,
)
from ..base_evaluator_agent import BaseEvaluatorAgent


class A2AEvaluatorAgent(BaseEvaluatorAgent):
    def __init__(
        self,
        evaluated_agent_address: str,
        transport: Optional[Transport],
        judge_llm: str,
        scenarios: Scenarios,
        business_context: Optional[str],
        headers: Optional[dict[str, str]] = None,
        judge_llm_auth: Optional[str] = None,
        debug: bool = False,
        deep_test_mode: bool = False,
        chat_update_callback: Optional[Callable[[dict], None]] = None,
        http_client: Optional[AsyncClient] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            evaluated_agent_address=evaluated_agent_address,
            protocol=Protocol.A2A,
            transport=transport,
            headers=headers,
            judge_llm=judge_llm,
            scenarios=scenarios,
            business_context=business_context,
            judge_llm_auth=judge_llm_auth,
            debug=debug,
            deep_test_mode=deep_test_mode,
            chat_update_callback=chat_update_callback,
            **kwargs,
        )
        self._http_client = http_client or AsyncClient(
            headers=headers or {},
            timeout=30,
        )
        self.__evaluated_agent_client: RemoteAgentConnections | None = None

    async def _get_evaluated_agent_client(self) -> RemoteAgentConnections:
        logger.debug("_get_evaluated_agent - enter")
        if self.__evaluated_agent_client is None:
            card_resolver = A2ACardResolver(
                self._http_client,
                self._evaluated_agent_address,
            )
            card = await card_resolver.get_agent_card()
            self.__evaluated_agent_client = RemoteAgentConnections(
                self._http_client,
                card,
            )

        return self.__evaluated_agent_client

    @staticmethod
    def _get_text_from_response(
        response: Task | Message | JSON_RPC_ERROR_TYPES,
    ) -> str | None:
        # TODO: add support for multi-model responses (audio, images, etc.)
        logger.debug(f"_get_text_from_response {response}")

        def get_parts_text(parts: list[Part]) -> str:
            text = ""
            for p in parts:
                if p.root.kind == "text":
                    text += p.root.text
                elif p.root.kind == "data":
                    text += json.dumps(p.root.data)
                elif p.root.kind == "file":
                    text += p.root.file.model_dump_json()

            return text

        if isinstance(response, Message):
            return get_parts_text(response.parts)
        elif isinstance(response, Task):
            if response.artifacts is None:
                if (
                    response.status is not None
                    and response.status.message is not None
                    and response.status.message.parts is not None
                ):
                    logger.debug("Returning text from task status message")
                    return get_parts_text(response.status.message.parts)
                return None

            artifacts_text = ""

            for artifact in response.artifacts:
                if artifact.name:
                    artifacts_text += f"Artifact: {artifact.name}:\n"
                artifacts_text += get_parts_text(artifact.parts)
                artifacts_text += "\n"

            return artifacts_text

        return None

    async def _send_message_to_evaluated_agent(
        self,
        context_id: str,
        message: str,
    ) -> dict[str, str]:
        """
        Sends a message to the evaluated agent.
        :param message: the text to send to the other agent.
        :param context_id: The context ID of the conversation.
            Each conversation has a unique context_id. All messages in the conversation
            have the same context_id.
        :return: A dictionary containing the response from the evaluated agent.
            - "response": the response string. If there is no response
                from the other agent, the string is empty.
        """
        try:
            logger.info(
                "🔗 Making A2A call to evaluated agent",
                extra={
                    "message": message[:100] + "..." if len(message) > 100 else message,
                    "context_id": context_id,
                    "agent_url": self._evaluated_agent_address,
                },
            )

            self._add_message_to_chat_history(context_id, "user", message)

            agent_client = await self._get_evaluated_agent_client()
            response = await agent_client.send_message(
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
            )

            if not response:
                logger.debug(
                    "_send_message_to_evaluated_agent - no response",
                    extra={"protocol": "a2a"},
                )
                return {"response": ""}

            agent_response_text = (
                self._get_text_from_response(response) or "Not a text response"
            )

            self._add_message_to_chat_history(
                context_id,
                "assistant",
                agent_response_text,
            )

            logger.info(
                "✅ A2A call successful - received response from evaluated agent",
                extra={
                    "response_length": len(agent_response_text),
                    "response_preview": (
                        agent_response_text[:100] + "..."
                        if len(agent_response_text) > 100
                        else agent_response_text
                    ),
                    "context_id": context_id,
                },
            )
            return {"response": response.model_dump_json()}
        except Exception as e:
            logger.exception(
                "❌ A2A call failed - error sending message to evaluated agent",
                extra={
                    "message": message[:100] + "..." if len(message) > 100 else message,
                    "context_id": context_id,
                    "agent_url": self._evaluated_agent_address,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return {"response": "", "error": str(e)}

    async def __aenter__(self) -> Self:
        await self._http_client.__aenter__()
        return await super().__aenter__()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await super().__aexit__(exc_type, exc_value, traceback)
        await self._http_client.__aexit__(exc_type, exc_value, traceback)
