from pydantic import BaseModel


class UserConfig(BaseModel):
    evaluated_agent_url: str
    authorization_header: str | None = None
    judge_model: str = "openai/gpt-4o"
    hugging_face_token: str | None = None
