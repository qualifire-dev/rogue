from enum import Enum
from typing import Optional
from pydantic import BaseModel, HttpUrl, SecretStr, root_validator, validator


class AuthType(Enum):
    NO_AUTH = "no_auth"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"


class AgentConfig(BaseModel):
    agent_url: HttpUrl
    auth_type: AuthType
    auth_credentials: Optional[SecretStr] = None
    judge_llm: str = "openai/o3-mini"
    judge_llm_api_key: SecretStr
    huggingface_api_key: SecretStr

    @root_validator(pre=True)
    def check_auth_credentials(cls, values):
        auth_type = values.get("auth_type")
        auth_credentials = values.get("auth_credentials")

        if auth_type != AuthType.NO_AUTH.value and not auth_credentials:
            raise ValueError(
                "Authentication Credentials cannot be empty for the selected auth type."
            )
        return values

    @validator("judge_llm_api_key", "huggingface_api_key", pre=True)
    def secret_must_not_be_empty(cls, v):
        if isinstance(v, SecretStr):
            v = v.get_secret_value()
        if not v:
            raise ValueError("This field cannot be empty.")
        return SecretStr(v)
