from pathlib import Path

from pydantic import BaseModel, model_validator, SecretStr, HttpUrl

from .config import AuthType
from .scenario import Scenarios


class CLIInput(BaseModel):
    """
    This is the actual model needed for the CLI.
    """

    workdir: Path = Path(".") / ".rogue"
    evaluated_agent_url: HttpUrl
    evaluated_agent_auth_type: AuthType = AuthType.NO_AUTH
    evaluated_agent_credentials: SecretStr | None = None
    judge_llm_model: str
    judge_llm_api_key: SecretStr | None = None
    input_scenarios_file: Path = workdir / "scenarios.json"
    output_report_file: Path = workdir / "report.md"
    business_context: str
    deep_test_mode: bool = False

    def get_scenarios_from_file(self) -> Scenarios:
        if not self.input_scenarios_file.exists():
            raise ValueError(
                f"Input scenarios file does not exist: {self.input_scenarios_file}"
            )
        if not self.input_scenarios_file.is_file():
            raise ValueError(
                f"Input scenarios file is not a file: {self.input_scenarios_file}"
            )

        return Scenarios.model_validate_json(self.input_scenarios_file.read_text())

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

    workdir: Path = Path(".") / ".rogue"
    evaluated_agent_url: HttpUrl | None = None
    evaluated_agent_auth_type: AuthType = AuthType.NO_AUTH
    evaluated_agent_credentials: SecretStr | None = None
    judge_llm_model: str | None = None
    judge_llm_api_key: SecretStr | None = None
    input_scenarios_file: Path = workdir / "scenarios.json"
    output_report_file: Path = workdir / "report.md"
    business_context: str | None = None
    business_context_file: Path = workdir / "business_context.md"
    deep_test_mode: bool = False
