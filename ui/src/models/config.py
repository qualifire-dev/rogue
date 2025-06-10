from enum import Enum
from typing import Optional

from pydantic import BaseModel, HttpUrl, SecretStr, field_validator
from pydantic_core.core_schema import ValidationInfo


class AuthType(Enum):
    NO_AUTH = "no_auth"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"


class AgentConfig(BaseModel):
    agent_url: HttpUrl
    auth_type: AuthType
    auth_credentials: Optional[SecretStr] = None
    judge_llm: str = "openai/gpt-4o"

    # This can be none when env is properly configured and/or in vertexai for example
    judge_llm_api_key: Optional[SecretStr] = None
    huggingface_api_key: Optional[SecretStr] = None

    # noinspection PyNestedDecorators
    @field_validator("auth_credentials", mode="after")
    @classmethod
    def check_auth_credentials(
        cld,
        value: Optional[SecretStr],
        info: ValidationInfo,
    ) -> Optional[SecretStr]:
        if info.data["auth_type"] != AuthType.NO_AUTH and not value:
            raise ValueError(
                "Authentication Credentials cannot be empty for the selected auth type."
            )
        return value
