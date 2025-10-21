from typing import Any

import pytest
from pydantic import HttpUrl, SecretStr, ValidationError
from pytest_mock import MockerFixture
from rogue_sdk.types import Protocol

from rogue.models.cli_input import AuthType, CLIInput


class TestCLIInput:
    @pytest.mark.parametrize(
        "auth_type, credentials, should_raise",
        [
            (AuthType.NO_AUTH, SecretStr("ignored"), False),
            (AuthType.API_KEY, SecretStr("key123"), False),
            (AuthType.BEARER_TOKEN, SecretStr("token"), False),
            (AuthType.BASIC_AUTH, SecretStr("user:pass"), False),
            (AuthType.NO_AUTH, None, False),
            (AuthType.API_KEY, None, True),
            (AuthType.BEARER_TOKEN, None, True),
            (AuthType.BASIC_AUTH, None, True),
        ],
    )
    def test_check_auth_credentials(self, auth_type, credentials, should_raise):
        input_data = {
            "evaluated_agent_url": "https://example.com",
            "evaluated_agent_auth_type": auth_type,
            "evaluated_agent_credentials": credentials,
            "judge_llm": "openai/o4-mini",
            "business_context": "Test",
        }

        if should_raise:
            with pytest.raises(
                ValidationError,
                match="Authentication Credentials cannot be empty",
            ):
                CLIInput(**input_data)
        else:
            model = CLIInput(**input_data)
            assert model.evaluated_agent_auth_type == auth_type
            assert model.evaluated_agent_credentials == credentials

    @pytest.mark.parametrize(
        "exists, is_file, file_content, should_raise",
        [
            (
                True,
                True,
                '{"scenarios": [{"scenario": "scenario1"}, {"scenario": "scenario2"}]}',
                False,
            ),
            (
                True,
                True,
                '{"scenarios": ["scenario1", "scenario2"]}',
                True,
            ),  # Not scenarios schema
            (True, True, None, True),  # Bad content
            (True, False, None, True),
            (False, False, None, True),
        ],
    )
    def test_get_scenarios_from_file(
        self,
        exists: bool,
        is_file: bool,
        file_content: str | None,
        should_raise: bool,
        mocker: MockerFixture,
    ):
        input_scenarios_file_mock = mocker.Mock()
        input_scenarios_file_mock.exists.return_value = exists
        input_scenarios_file_mock.is_file.return_value = is_file
        input_scenarios_file_mock.read_text.return_value = file_content

        class CLIInputWithMockScenarios(CLIInput):
            input_scenarios_file: (
                Any  # Just to avoid pydantic validation error on the mock
            )

        cli_input = CLIInputWithMockScenarios(
            protocol=Protocol.A2A,
            evaluated_agent_url=HttpUrl("https://example.com"),
            judge_llm="example-model",
            business_context="example-context",
            input_scenarios_file=input_scenarios_file_mock,
        )

        if should_raise:
            with pytest.raises((ValueError, ValidationError)):
                cli_input.get_scenarios_from_file()
        else:
            scenarios = cli_input.get_scenarios_from_file()
            assert scenarios is not None
