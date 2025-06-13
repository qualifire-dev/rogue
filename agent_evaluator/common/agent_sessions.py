from uuid import uuid4

from google.adk.sessions import Session, BaseSessionService


async def create_session(
    app_name: str,
    session_service: BaseSessionService,
    user_id: str | None = None,
) -> Session:
    user_id = user_id or uuid4().hex
    return await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=uuid4().hex,
    )
