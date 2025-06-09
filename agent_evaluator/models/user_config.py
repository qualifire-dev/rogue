from pydantic import BaseModel


class UserConfig(BaseModel):
    evaluated_agent_url: str
    authorization_header: str | None = None
    agent_model: str = "openai/gpt-4o"
