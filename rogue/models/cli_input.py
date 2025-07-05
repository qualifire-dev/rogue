from pathlib import Path

from pydantic import BaseModel, model_validator, field_validator

from .config import AuthType


class CLIInput(BaseModel):
    """
    This is the actual model needed for the CLI.
    """

    evaluated_agent_url: str
    evaluated_agent_auth_type: AuthType = AuthType.NO_AUTH
    evaluated_agent_credentials: str | None = None
    judge_llm_model: str
    judge_llm_api_key: str | None = None
    input_scenarios_file: Path
    output_report_file: Path
    business_context: str
    deep_test_mode: bool = False

    # noinspection PyNestedDecorators
    @field_validator("input_scenarios_file", mode="after")
    @classmethod
    def validate_input_scenarios_file(cls, value: Path) -> Path:
        if not value.exists():
            raise ValueError(f"Input scenarios file does not exist: {value}")
        if not value.is_file():
            raise ValueError(f"Input scenarios file is not a file: {value}")
        return value

    @model_validator(mode="after")
    def check_auth_credentials(self) -> "CLIInput":
        auth_type = self.evaluated_agent_auth_type
        auth_credentials = self.evaluated_agent_credentials

        if auth_type != AuthType.NO_AUTH and not auth_credentials:
            raise ValueError(
                "Authentication Credentials cannot be empty for the selected auth type."
            )
        return self


class PartialCLIInput(BaseModel):
    """
    This is a partial model that is used to validate the CLI input.
    This is used to allow the user to provide both a config file and CLI arguments.
    """

    evaluated_agent_url: str | None = None
    evaluated_agent_auth_type: AuthType | None = None
    evaluated_agent_credentials: str | None = None
    judge_llm_model: str | None = None
    judge_llm_api_key: str | None = None
    input_scenarios_file: Path | None = None
    output_report_file: Path | None = None
    business_context: str | None = None
    business_context_file: Path | None = None
    deep_test_mode: bool | None = None
