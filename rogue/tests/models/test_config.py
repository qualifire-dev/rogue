import pytest
from pydantic import ValidationError

from rogue.models.config import (
    AgentConfig,
    AuthType,
    get_auth_header,
)


@pytest.mark.parametrize(
    "auth_type, auth_credentials, should_raise",
    [
        (AuthType.NO_AUTH, "should be ignored", False),
        (AuthType.API_KEY, "abc123", False),
        (AuthType.BEARER_TOKEN, "token456", False),
        (AuthType.BASIC_AUTH, "user:pass", False),
        (AuthType.NO_AUTH, None, False),
        (AuthType.API_KEY, None, True),
        (AuthType.BEARER_TOKEN, None, True),
        (AuthType.BASIC_AUTH, None, True),
    ],
)
def test_check_auth_credentials(
    auth_type: str,
    auth_credentials: str | None,
    should_raise: bool,
):
    config_data = {
        "evaluated_agent_url": "https://example.com",
        "evaluated_agent_auth_type": auth_type,
        "evaluated_agent_credentials": auth_credentials,
    }

    if should_raise:
        with pytest.raises(
            ValidationError,
            match="Authentication Credentials cannot be empty",
        ):
            AgentConfig(**config_data)  # type: ignore
    else:
        config = AgentConfig(**config_data)  # type: ignore
        assert config.auth_type == auth_type
        assert config.auth_credentials == auth_credentials


@pytest.mark.parametrize(
    "auth_type, auth_credentials, expected_header",
    [
        (AuthType.NO_AUTH, "should be ignored", {}),
        (AuthType.API_KEY, "key123", {"X-API-Key": "key123"}),
        (AuthType.BEARER_TOKEN, "token456", {"Authorization": "Bearer token456"}),
        (AuthType.BASIC_AUTH, "user:pass", {"Authorization": "Basic user:pass"}),
        (AuthType.NO_AUTH, None, {}),
        (AuthType.API_KEY, None, {}),
        (AuthType.BEARER_TOKEN, None, {}),
        (AuthType.BASIC_AUTH, None, {}),
    ],
)
def test_get_auth_header(auth_type, auth_credentials, expected_header):
    header = get_auth_header(auth_type, auth_credentials)
    assert header == expected_header
