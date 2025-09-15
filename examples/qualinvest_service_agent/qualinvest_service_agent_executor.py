import base64
from logging import getLogger
from typing import AsyncGenerator

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCard,
    TaskState,
    UnsupportedOperationError,
    Part,
    TextPart,
    FilePart,
    FileWithUri,
    FileWithBytes,
)
from a2a.utils.errors import ServerError
from google.adk import Runner
from google.adk.events import Event
from google.genai import types

logger = getLogger(__name__)


class investifyAgentExecutor(AgentExecutor):
    """An AgentExecutor that runs an ADK-based Agent."""

    def __init__(self, runner: Runner, card: AgentCard):
        self.runner = runner
        self._card = card

        self._running_sessions = {}  # type: ignore

    def _run_agent(
        self,
        session_id,
        new_message: types.Content,
    ) -> AsyncGenerator[Event, None]:
        return self.runner.run_async(
            session_id=session_id,
            user_id="self",
            new_message=new_message,
        )

    async def _process_request(
        self,
        new_message: types.Content,
        session_id: str,
        task_updater: TaskUpdater,
    ) -> None:
        # The call to self._upsert_session was returning a coroutine object,
        # leading to an AttributeError when trying to access .id on it directly.
        # We need to await the coroutine to get the actual session object.
        session_obj = await self._upsert_session(
            session_id,
        )
        # Update session_id with the ID from the resolved session object
        # to be used in self._run_agent.
        session_id = session_obj.id

        async for event in self._run_agent(session_id, new_message):
            if event.is_final_response():
                if event.content:
                    parts = convert_genai_parts_to_a2a(event.content.parts)
                    logger.debug(f"Yielding final response. parts: {parts}")
                    await task_updater.add_artifact(parts)
                await task_updater.complete()
                break
            if not event.get_function_calls() and event.content:
                logger.debug("Yielding update response")
                await task_updater.update_status(
                    TaskState.working,
                    message=task_updater.new_agent_message(
                        convert_genai_parts_to_a2a(event.content.parts),
                    ),
                )
            else:
                logger.debug("Skipping event")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        # Run the agent until either complete or the task is suspended.
        updater = TaskUpdater(
            event_queue,
            context.task_id or "",
            context.context_id or "",
        )
        # Immediately notify that the task is submitted.
        if not context.current_task:
            await updater.submit()
        await updater.start_work()

        if context.message is not None:
            await self._process_request(
                types.UserContent(
                    parts=convert_a2a_parts_to_genai(context.message.parts),
                ),
                context.context_id or "",
                updater,
            )
        logger.debug("investifyAgent execute exiting")

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        # Ideally: kill any ongoing tasks.
        raise ServerError(error=UnsupportedOperationError())

    async def _upsert_session(self, session_id: str):
        """
        Retrieves a session if it exists, otherwise creates a new one.
        Ensures that async session service methods are properly awaited.
        """
        session = await self.runner.session_service.get_session(
            app_name=self.runner.app_name,
            user_id="self",
            session_id=session_id,
        )
        if session is None:
            session = await self.runner.session_service.create_session(
                app_name=self.runner.app_name,
                user_id="self",
                session_id=session_id,
            )
        # According to ADK InMemorySessionService,
        # create_session should always return a Session object.
        if session is None:
            logger.error(
                f"Critical error: Session is None even after "
                f"create_session for session_id: {session_id}",
            )
            raise RuntimeError(
                f"Failed to get or create session: {session_id}",
            )
        return session


def convert_a2a_parts_to_genai(parts: list[Part]) -> list[types.Part]:
    """Convert a list of A2A Part types into a list of Google Gen AI Part types."""
    return [convert_a2a_part_to_genai(part) for part in parts]


def convert_a2a_part_to_genai(part: Part) -> types.Part:
    """Convert a single A2A Part type into a Google Gen AI Part type."""
    part = part.root  # type: ignore
    if isinstance(part, TextPart):
        return types.Part(text=part.text)
    if isinstance(part, FilePart):
        if isinstance(part.file, FileWithUri):
            return types.Part(
                file_data=types.FileData(
                    file_uri=part.file.uri,
                    mime_type=part.file.mimeType,
                ),
            )
        if isinstance(part.file, FileWithBytes):
            return types.Part(
                inline_data=types.Blob(
                    data=base64.b64decode(part.file.bytes),
                    mime_type=part.file.mimeType,
                ),
            )
        raise ValueError(f"Unsupported file type: {type(part.file)}")
    raise ValueError(f"Unsupported part type: {type(part)}")


def convert_genai_parts_to_a2a(parts: list[types.Part] | None) -> list[Part]:
    """Convert a list of Google Gen AI Part types into a list of A2A Part types."""
    parts = parts or []
    return [
        convert_genai_part_to_a2a(part)
        for part in parts
        if (part.text or part.file_data or part.inline_data)
    ]


def convert_genai_part_to_a2a(part: types.Part) -> Part:
    """Convert a single Google Gen AI Part type into an A2A Part type."""
    if part.text:
        return Part(root=TextPart(text=part.text))
    if part.file_data:
        return Part(
            root=FilePart(
                file=FileWithUri(
                    uri=part.file_data.file_uri or "",
                    mimeType=part.file_data.mime_type,
                ),
            ),
        )
    if part.inline_data:
        return Part(
            root=FilePart(
                file=FileWithBytes(
                    bytes=base64.b64encode(
                        part.inline_data.data,  # type: ignore
                    ).decode(),
                    mimeType=part.inline_data.mime_type,
                ),
            ),
        )
    raise ValueError(f"Unsupported part type: {part}")
