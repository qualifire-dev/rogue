import json
from argparse import Namespace
from pathlib import Path

import pytest
from pydantic import HttpUrl, SecretStr
from pytest_mock import MockerFixture
from rogue_sdk.types import AuthType

from rogue.models.cli_input import CLIInput
from rogue.run_cli import get_cli_input


@pytest.mark.parametrize(
    "config_file_content, cli_args, expected",
    [
        (  # No config file
            None,
            Namespace(
                evaluated_agent_url="https://localhost:10001",
                business_context="my business",
                judge_llm="openai/o4-mini",
            ),
            CLIInput(
                workdir=Path(".") / ".rogue",
                evaluated_agent_url=HttpUrl("https://localhost:10001"),
                evaluated_agent_auth_type=AuthType.NO_AUTH,
                evaluated_agent_credentials=None,
                judge_llm="openai/o4-mini",
                judge_llm_api_key=None,
                input_scenarios_file=Path(".") / ".rogue" / "scenarios.json",
                output_report_file=Path(".") / ".rogue" / "report.md",
                business_context="my business",
                deep_test_mode=False,
            ),
        ),
        (  # Only config file
            {
                "agent_url": "https://localhost:10001",
                "auth_type": "api_key",
                "auth_credentials": "abc123",
            },
            # business context isn't in the config file,
            # so it must be provided using a file or hardcoded string
            Namespace(business_context="my business"),
            CLIInput(
                workdir=Path(".") / ".rogue",
                evaluated_agent_url=HttpUrl("https://localhost:10001"),
                evaluated_agent_auth_type=AuthType.API_KEY,
                evaluated_agent_credentials=SecretStr("abc123"),
                judge_llm="openai/o4-mini",
                judge_llm_api_key=None,
                input_scenarios_file=Path(".") / ".rogue" / "scenarios.json",
                output_report_file=Path(".") / ".rogue" / "report.md",
                business_context="my business",
                deep_test_mode=False,
            ),
        ),
        (  # Both config file and CLI args
            {
                "agent_url": "https://localhost:10001",
            },
            Namespace(
                evaluated_agent_url="https://overriden_agent_url:10001",
                business_context="my business",
            ),
            CLIInput(
                workdir=Path(".") / ".rogue",
                evaluated_agent_url=HttpUrl("https://overriden_agent_url:10001"),
                evaluated_agent_auth_type=AuthType.NO_AUTH,
                evaluated_agent_credentials=None,
                judge_llm="openai/o4-mini",
                judge_llm_api_key=None,
                input_scenarios_file=Path(".") / ".rogue" / "scenarios.json",
                output_report_file=Path(".") / ".rogue" / "report.md",
                business_context="my business",
                deep_test_mode=False,
            ),
        ),
    ],
)
def test_get_cli_input(
    config_file_content: dict[str, str] | None,
    cli_args: Namespace | None,
    expected: CLIInput,
    mocker: MockerFixture,
):
    config_file = mocker.Mock()
    if config_file_content:
        config_file.is_file.return_value = True
        config_file.read_text.return_value = json.dumps(config_file_content)
    else:
        config_file.is_file.return_value = False

    if cli_args is None:
        cli_args = Namespace()

    cli_args.config_file = config_file

    assert get_cli_input(cli_args) == expected
