from typing import Callable, TypeAlias
from uuid import uuid4

import httpx
from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    Task,
    Message,
    MessageSendParams,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    SendMessageRequest,
    SendStreamingMessageRequest,
    JSONRPCErrorResponse,
    JSONRPCError,
    JSONParseError,
    InvalidRequestError,
    MethodNotFoundError,
    InvalidParamsError,
    InternalError,
    TaskNotFoundError,
    TaskNotCancelableError,
    PushNotificationNotSupportedError,
    UnsupportedOperationError,
    ContentTypeNotSupportedError,
    InvalidAgentResponseError,
)
from loguru import logger

from .generic_task_callback import GenericTaskUpdateCallback

JSON_RPC_ERROR_TYPES: TypeAlias = (
    JSONRPCError
    | JSONParseError
    | InvalidRequestError
    | MethodNotFoundError
    | InvalidParamsError
    | InternalError
    | TaskNotFoundError
    | TaskNotCancelableError
    | PushNotificationNotSupportedError
    | UnsupportedOperationError
    | ContentTypeNotSupportedError
    | InvalidAgentResponseError
)

TaskCallbackArg: TypeAlias = Task | TaskStatusUpdateEvent | TaskArtifactUpdateEvent
TaskUpdateCallback: TypeAlias = Callable[[TaskCallbackArg, AgentCard], Task]


class RemoteAgentConnections:
    """A class to hold the connections to the remote agents."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        agent_card: AgentCard,
    ):
        self.agent_client = A2AClient(client, agent_card)
        self.card = agent_card

    def get_agent(self) -> AgentCard:
        return self.card

    async def send_message(
        self,
        request: MessageSendParams,
        task_callback: TaskUpdateCallback | None = None,
        stream: bool | None = None,
    ) -> Task | Message | JSON_RPC_ERROR_TYPES | None:
        if stream is None:  # defaults to stream if the other agent supports it
            stream = self.card.capabilities.streaming

        if task_callback is None:
            task_callback = GenericTaskUpdateCallback().task_callback

        if stream:
            task = None
            async for stream_response in self.agent_client.send_message_streaming(
                SendStreamingMessageRequest(
                    id=uuid4().hex,
                    params=request,
                )
            ):
                logger.debug(
                    "received stream response from remote agent",
                    extra={
                        "response": stream_response,
                    },
                )

                if isinstance(stream_response.root, JSONRPCErrorResponse):
                    return stream_response.root.error

                # In the case a message is returned, that is the end of the interaction.
                event = stream_response.root.result
                if isinstance(event, Message):
                    return event

                # Otherwise we are in the Task + TaskUpdate cycle.
                if task_callback is not None and event:
                    task = task_callback(event, self.card)
                if hasattr(event, "final") and event.final:
                    break

            return task
        else:  # Non-streaming
            response = await self.agent_client.send_message(
                SendMessageRequest(
                    id=uuid4().hex,
                    params=request,
                )
            )

            logger.debug(
                "received non-stream response from remote agent",
                extra={
                    "response": response,
                },
            )

            if isinstance(response.root, JSONRPCErrorResponse):
                return response.root.error
            if isinstance(response.root.result, Message):
                return response.root.result

            if task_callback is not None:
                task_callback(response.root.result, self.card)
            return response.root.result
