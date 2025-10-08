from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from google.adk.sessions import BaseSessionService, Session


async def create_session(
    app_name: str,
    session_service: "BaseSessionService",
    user_id: str | None = None,
) -> "Session":
    user_id = user_id or uuid4().hex
    return await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=uuid4().hex,
    )
