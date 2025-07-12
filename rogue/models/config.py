from enum import Enum
from typing import Optional

from pydantic import BaseModel, HttpUrl, model_validator, ConfigDict, Field


class AuthType(Enum):
    NO_AUTH = "no_auth"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"  # nosec: B105
    BASIC_AUTH = "basic"


class AgentConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    agent_url: HttpUrl = Field(alias="evaluated_agent_url")
    auth_type: AuthType = Field(
        alias="evaluated_agent_auth_type",
        default=AuthType.NO_AUTH,
    )
    auth_credentials: Optional[str] = Field(
        alias="evaluated_agent_credentials",
        default=None,
    )
    service_llm: str = "openai/gpt-4.1"
    judge_llm: str = Field(alias="judge_llm_model", default="openai/o4-mini")
    interview_mode: bool = True
    deep_test_mode: bool = False
    parallel_runs: int = 1

    # This can be none when env is properly configured and/or in vertexai for example
    judge_llm_api_key: Optional[str] = None
    # huggingface_api_key: Optional[str] = None

    @model_validator(mode="after")
    def check_auth_credentials(self) -> "AgentConfig":
        auth_type = self.auth_type
        auth_credentials = self.auth_credentials

        if auth_type and auth_type != AuthType.NO_AUTH and not auth_credentials:
            raise ValueError(
                "Authentication Credentials cannot be empty for the selected auth type."
            )
        return self


def get_auth_header(
    auth_type: AuthType,
    auth_credentials: Optional[str],
) -> dict[str, str]:
    if auth_type == AuthType.NO_AUTH or not auth_credentials:
        return {}
    elif auth_type == AuthType.API_KEY:
        return {"X-API-Key": auth_credentials}
    elif auth_type == AuthType.BEARER_TOKEN:
        return {"Authorization": f"Bearer {auth_credentials}"}
    elif auth_type == AuthType.BASIC_AUTH:
        return {"Authorization": f"Basic {auth_credentials}"}
    return {}
