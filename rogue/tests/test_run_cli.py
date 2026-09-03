import asyncio
import json
from argparse import Namespace
from pathlib import Path

import pytest
from pydantic import HttpUrl, SecretStr
from pytest_mock import MockerFixture

from rogue.models.cli_input import CLIInput
from rogue.run_cli import get_a2a_agent_card, get_cli_input
from rogue_sdk.types import AuthType, Protocol, Transport


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
                protocol=Protocol.A2A,
                transport=Transport.HTTP,
                evaluated_agent_url=HttpUrl("https://localhost:10001"),
                evaluated_agent_auth_type=AuthType.NO_AUTH,
                evaluated_agent_credentials=None,
                judge_llm="openai/o4-mini",
                judge_llm_api_key=None,
                input_scenarios_file=Path(".") / ".rogue" / "scenarios.json",
                output_report_file=Path(".") / ".rogue" / "report.md",
                business_context="my business",
            ),
        ),
        (  # Only config file
            {
                "evaluated_agent_url": "https://localhost:10001",
                "evaluated_agent_auth_type": "api_key",
                "evaluated_agent_credentials": "abc123",
            },
            # business context isn't in the config file,
            # so it must be provided using a file or hardcoded string
            Namespace(business_context="my business"),
            CLIInput(
                workdir=Path(".") / ".rogue",
                protocol=Protocol.A2A,
                transport=Transport.HTTP,
                evaluated_agent_url=HttpUrl("https://localhost:10001"),
                evaluated_agent_auth_type=AuthType.API_KEY,
                evaluated_agent_credentials=SecretStr("abc123"),
                judge_llm="openai/o4-mini",
                judge_llm_api_key=None,
                input_scenarios_file=Path(".") / ".rogue" / "scenarios.json",
                output_report_file=Path(".") / ".rogue" / "report.md",
                business_context="my business",
            ),
        ),
        (  # Both config file and CLI args
            {
                "evaluated_agent_url": "https://localhost:10001",
            },
            Namespace(
                evaluated_agent_url="https://overriden_agent_url:10001",
                business_context="my business",
            ),
            CLIInput(
                workdir=Path(".") / ".rogue",
                protocol=Protocol.A2A,
                transport=Transport.HTTP,
                evaluated_agent_url=HttpUrl("https://overriden_agent_url:10001"),
                evaluated_agent_auth_type=AuthType.NO_AUTH,
                evaluated_agent_credentials=None,
                judge_llm="openai/o4-mini",
                judge_llm_api_key=None,
                input_scenarios_file=Path(".") / ".rogue" / "scenarios.json",
                output_report_file=Path(".") / ".rogue" / "report.md",
                business_context="my business",
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


_AGENT_CARD_JSON = {
    "name": "test-agent",
    "description": "A test agent",
    "url": "https://localhost:10001",
    "version": "0.2.0",
    "capabilities": {"streaming": False, "pushNotifications": False},
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
    "skills": [],
}


@pytest.mark.parametrize(
    "transport",
    [
        Transport.HTTP,
        Transport.STREAMABLE_HTTP,
        Transport.SSE,
    ],
)
def test_get_a2a_agent_card_accepts_http_transports(
    transport: Transport,
    mocker: MockerFixture,
):
    """Regression test for issue #150.

    The A2A agent card is served over HTTP at the well-known path regardless of
    the RPC transport, so STREAMABLE_HTTP/SSE must not raise
    'Unsupported transport'. Before the fix only Transport.HTTP was accepted.
    """
    mock_get = mocker.patch("rogue.run_cli.requests.get")
    mock_get.return_value.json.return_value = _AGENT_CARD_JSON
    mock_get.return_value.status_code = 200

    card = asyncio.run(
        get_a2a_agent_card(agent_url="https://localhost:10001", transport=transport)
    )
    assert card is not None
    assert card.name == "test-agent"
    mock_get.assert_called_once()


def test_get_a2a_agent_card_rejects_unsupported_transport(mocker: MockerFixture):
    """Non-HTTP transports for A2A (e.g. CHAT_COMPLETIONS) still raise."""
    mock_get = mocker.patch("rogue.run_cli.requests.get")
    with pytest.raises(ValueError):
        asyncio.run(
            get_a2a_agent_card(
                agent_url="https://localhost:10001",
                transport=Transport.CHAT_COMPLETIONS,
            )
        )
    mock_get.assert_not_called()
