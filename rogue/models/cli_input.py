from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, SecretStr, model_validator
from rogue_sdk.types import AuthType, EvaluationMode, Protocol, Scenarios, Transport


class CLIInput(BaseModel):
    """
    This is the actual model needed for the CLI.
    """

    workdir: Path = Path(".") / ".rogue"
    protocol: Protocol
    transport: Transport | None = None  # None for PYTHON protocol
    evaluated_agent_url: HttpUrl | None = None  # Optional for PYTHON protocol
    evaluated_agent_auth_type: AuthType = AuthType.NO_AUTH
    evaluated_agent_credentials: SecretStr | None = None
    python_entrypoint_file: Path | None = None  # For PYTHON protocol
    judge_llm: str
    judge_llm_api_key: SecretStr | None = None
    qualifire_api_key: SecretStr | None = None
    input_scenarios_file: Path = workdir / "scenarios.json"
    output_report_file: Path = workdir / "report.md"
    business_context: str
    deep_test_mode: bool = False
    evaluation_mode: EvaluationMode = EvaluationMode.POLICY
    owasp_categories: Optional[List[str]] = None
    attacks_per_category: int = 5
    min_tests_per_attack: int = 3

    def get_scenarios_from_file(self) -> Scenarios:
        if not self.input_scenarios_file.exists():
            raise ValueError(
                f"Input scenarios file does not exist: {self.input_scenarios_file}",
            )
        if not self.input_scenarios_file.is_file():
            raise ValueError(
                f"Input scenarios file is not a file: {self.input_scenarios_file}",
            )

        return Scenarios.model_validate_json(self.input_scenarios_file.read_text())

    @model_validator(mode="after")
    def check_auth_credentials(self) -> "CLIInput":
        auth_type = self.evaluated_agent_auth_type
        auth_credentials = self.evaluated_agent_credentials

        if auth_type != AuthType.NO_AUTH and not auth_credentials:
            raise ValueError(
                "Authentication Credentials cannot be empty for the selected auth type.",  # noqa: E501
            )
        return self

    @model_validator(mode="after")
    def check_red_team_mode(self) -> "CLIInput":
        """Validate that OWASP categories are provided in red team mode."""
        if (
            self.evaluation_mode == EvaluationMode.RED_TEAM
            and not self.owasp_categories
        ):
            raise ValueError(
                "owasp_categories must be provided when evaluation_mode is 'red_team'",
            )
        return self

    @model_validator(mode="after")
    def check_protocol_requirements(self) -> "CLIInput":
        """Validate protocol-specific requirements."""
        if self.protocol == Protocol.PYTHON:
            if not self.python_entrypoint_file:
                raise ValueError(
                    "python_entrypoint_file is required when protocol is PYTHON",
                )
            if not self.python_entrypoint_file.exists():
                raise ValueError(
                    f"Python entrypoint file does not exist: {self.python_entrypoint_file}",  # noqa: E501
                )
            if not self.python_entrypoint_file.is_file():
                raise ValueError(
                    f"Python entrypoint path is not a file: {self.python_entrypoint_file}",  # noqa: E501
                )
        else:
            if not self.evaluated_agent_url:
                raise ValueError(
                    "evaluated_agent_url is required when protocol is not PYTHON",
                )
            if self.transport is None:
                raise ValueError(
                    "transport is required when protocol is not PYTHON",
                )
        return self


class PartialCLIInput(BaseModel):
    """
    This is a partial model that is used to validate the CLI input.
    This is used to allow the user to provide both a config file and CLI arguments.
    """

    workdir: Path = Path(".") / ".rogue"
    protocol: Protocol = Field(default=Protocol.A2A)
    transport: Transport = None  # type: ignore # fixed in model_post_init
    evaluated_agent_url: HttpUrl | None = Field(default=None)
    evaluated_agent_auth_type: AuthType = Field(default=AuthType.NO_AUTH)
    evaluated_agent_credentials: SecretStr | None = Field(default=None)
    python_entrypoint_file: Path | None = Field(default=None)  # For PYTHON protocol
    judge_llm: str | None = None
    judge_llm_api_key: SecretStr | None = None
    business_context: str | None = None
    business_context_file: Path = None  # type: ignore # fixed in model_post_init
    input_scenarios_file: Path = None  # type: ignore # fixed in model_post_init
    output_report_file: Path = None  # type: ignore # fixed in model_post_init
    deep_test_mode: bool = False
    evaluation_mode: EvaluationMode = Field(default=EvaluationMode.POLICY)
    owasp_categories: Optional[List[str]] = None
    attacks_per_category: int = Field(default=5)
    min_tests_per_attack: int = Field(default=3)
    qualifire_api_key: SecretStr | None = None

    def model_post_init(self, __context):
        # Set defaults based on workdir if not provided
        # This must be done in instance creation and not in the model itself
        if self.input_scenarios_file is None:
            self.input_scenarios_file = self.workdir / "scenarios.json"
        if self.output_report_file is None:
            self.output_report_file = self.workdir / "report.md"
        if self.business_context_file is None:
            self.business_context_file = self.workdir / "business_context.md"

        if self.transport is None:
            self.transport = self.protocol.get_default_transport()
