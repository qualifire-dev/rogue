import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard

from .models.user_config import UserConfig


def get_config_from_ui() -> UserConfig:
    # this is a placeholder for now
    return UserConfig(
        evaluated_agent_url="http://localhost:10001",
        authorization_header=None,
        judge_model="openai/gpt-4o",
    )


async def get_evaluated_agent_card(config: UserConfig) -> AgentCard:
    headers = (
        {"Authorization": config.authorization_header}
        if config.authorization_header
        else {}
    )

    async with httpx.AsyncClient(headers=headers) as http_client:
        card_resolver = A2ACardResolver(
            http_client,
            config.evaluated_agent_url,
        )
        return await card_resolver.get_agent_card()


async def run_cli(
    evaluated_agent_url: str,
    input_scenarios_file: str,
    output_report_file: str,
):
    # TODO
    return
