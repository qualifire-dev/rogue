"""
Regression tests for issue #179: A2A red team attacker must send auth headers.

The A2ARedTeamAttackerAgent builds an httpx.AsyncClient used for both the
agent-card fetch (A2ACardResolver) and every attack message. When the evaluated
agent requires auth (API key / bearer / basic), that client must carry the
resolved auth headers; otherwise authenticated A2A agents can't be red-teamed
(the card GET returns 401 and the scan fails to start).

These tests also cover the CWE-319 hardening introduced alongside #179: API-key
/ bearer credentials must never be transmitted over a cleartext (http://) URL.
"""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest

from rogue.evaluator_agent.red_team.a2a_red_team_attacker_agent import (
    A2ARedTeamAttackerAgent,
)
from rogue.server.red_teaming.models import RedTeamConfig, ScanType
from rogue_sdk.types import AuthType, Protocol, Transport


def _make_agent(
    auth_type: AuthType,
    credentials: str | None,
    address: str = "http://localhost:9999",
) -> A2ARedTeamAttackerAgent:
    red_team_config = RedTeamConfig(scan_type=ScanType.BASIC)
    return A2ARedTeamAttackerAgent(
        evaluated_agent_address=address,
        protocol=Protocol.A2A,
        transport=Transport.HTTP,
        auth_type=auth_type,
        auth_credentials=credentials,
        red_team_config=red_team_config,
        business_context="test",
        attacker_llm="gpt-4",
        attacker_llm_auth=None,
        attacker_llm_aws_access_key_id=None,
        attacker_llm_aws_secret_access_key=None,
        attacker_llm_aws_region=None,
        judge_llm="gpt-4",
        judge_llm_auth=None,
        judge_llm_aws_access_key_id=None,
        judge_llm_aws_secret_access_key=None,
        judge_llm_aws_region=None,
        rogue_security_api_key=None,
    )


def _patch_network(mocker) -> None:
    mocker.patch(
        "rogue.evaluator_agent.red_team.a2a_red_team_attacker_agent.A2ACardResolver",
        return_value=MagicMock(get_agent_card=AsyncMock(return_value=MagicMock())),
    )
    mocker.patch(
        "rogue.evaluator_agent.red_team.a2a_red_team_attacker_agent."
        "RemoteAgentConnections",
        return_value=MagicMock(),
    )


@pytest.mark.asyncio
async def test_a2a_client_sends_api_key_header(mocker):
    """API key auth must be propagated to the A2A http client."""
    _patch_network(mocker)
    agent = _make_agent(AuthType.API_KEY, "secret-key-123", "https://localhost:9999")
    async with agent:
        client = agent._http_client
        assert client is not None
        assert client.headers.get("X-API-Key") == "secret-key-123"


@pytest.mark.asyncio
async def test_a2a_client_sends_bearer_header(mocker):
    """Bearer auth must be propagated to the A2A http client."""
    _patch_network(mocker)
    agent = _make_agent(AuthType.BEARER_TOKEN, "tok-abc", "https://localhost:9999")
    async with agent:
        client = agent._http_client
        assert client is not None
        assert client.headers.get("Authorization") == "Bearer tok-abc"


@pytest.mark.asyncio
async def test_a2a_client_empty_headers_for_no_auth(mocker):
    """NO_AUTH must not inject any auth header (HTTP allowed)."""
    _patch_network(mocker)
    agent = _make_agent(AuthType.NO_AUTH, None, "http://localhost:9999")
    async with agent:
        client = agent._http_client
        assert client is not None
        assert "X-API-Key" not in client.headers
        assert not any(h.lower() == "authorization" for h in client.headers)


@pytest.mark.asyncio
async def test_a2a_rejects_cleartext_http_with_auth(mocker):
    """API key over http:// must be rejected (CWE-319)."""
    _patch_network(mocker)
    os.environ.pop("ROGUE_ALLOW_INSECURE_AGENT_HTTP", None)
    agent = _make_agent(AuthType.API_KEY, "secret-key-123", "http://localhost:9999")
    with pytest.raises(ValueError, match="non-HTTPS"):
        async with agent:
            pass


@pytest.mark.asyncio
async def test_a2a_allows_cleartext_http_with_auth_override(mocker):
    """Dev override permits credentials over http:// when explicitly set."""
    _patch_network(mocker)
    os.environ["ROGUE_ALLOW_INSECURE_AGENT_HTTP"] = "1"
    try:
        agent = _make_agent(AuthType.API_KEY, "secret-key-123", "http://localhost:9999")
        async with agent:
            client = agent._http_client
            assert client is not None
            assert client.headers.get("X-API-Key") == "secret-key-123"
    finally:
        os.environ.pop("ROGUE_ALLOW_INSECURE_AGENT_HTTP", None)
