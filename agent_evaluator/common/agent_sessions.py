from uuid import uuid4

from google.adk.sessions import Session


def create_session() -> Session:
    return Session(
        id=uuid4().hex,
        user_id=uuid4().hex,
    )
