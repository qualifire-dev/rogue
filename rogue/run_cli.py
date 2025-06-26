import httpx
from a2a.client import A2ACardResolver
from a2a.types import AgentCard
from google.adk import Runner
from google.adk.agents import BaseAgent, SequentialAgent
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types
from loguru import logger

from .common.agent_sessions import create_session
from .models.user_config import UserConfig
from .orchestrator_agent.orchestrator_agent import OrchestratorAgentFactory


def get_config_from_ui() -> UserConfig:
    # this is a placeholder for now
    return UserConfig(
        evaluated_agent_url="http://localhost:10001",
        authorization_header=None,
        model="openai/gpt-4o",
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


def create_scenario_generation_agent(card: AgentCard, model: str) -> BaseAgent:
    # TODO: dror
    pass


def create_evaluator_agent(card: AgentCard) -> BaseAgent:
    # TODO: yuval
    pass


def create_report_generation_agent() -> BaseAgent:
    # TODO: yuval
    pass


def create_orchestrator_agent(
    scenario_generation_agent: BaseAgent,
    evaluator_agent: BaseAgent,
    report_generation_agent: BaseAgent,
) -> SequentialAgent:
    return OrchestratorAgentFactory(
        scenario_generation_agent=scenario_generation_agent,
        evaluator_agent=evaluator_agent,
        report_generation_agent=report_generation_agent,
    ).create_agent()


def run_sequential_agent(
    sequential_agent_runner: Runner,
    input_text: str,
    session: Session | None = None,
) -> None:
    session = session or create_session()

    # Create content from user input
    content = types.Content(
        role="user",
        parts=[types.Part(text=input_text)],
    )
    # Run the agent with the runner
    for event in sequential_agent_runner.run(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content,
    ):
        try:
            logger.info(f"orchestration_agent response: {event.content.parts[0].text}")
        except Exception:
            pass  # Not continue, we want the "done" log

        if event.is_final_response():
            logger.info(f"orchestration_agent done")


async def run_cli(
    evaluated_agent_url: str,
    input_scenarios_file: str,
    output_report_file: str,
):
    # TODO: fix

    config = get_config_from_ui()

    card = await get_evaluated_agent_card(config)
    scenario_generation_agent = create_scenario_generation_agent(card, config.model)
    evaluator_agent = create_evaluator_agent(card)
    report_generation_agent = create_report_generation_agent()

    # For ADK tools compatibility, the root agent must be named `root_agent`
    root_agent = create_orchestrator_agent(
        scenario_generation_agent=scenario_generation_agent,
        evaluator_agent=evaluator_agent,
        report_generation_agent=report_generation_agent,
    )

    root_agent_runner = Runner(
        app_name="agent_evaluator",
        agent=root_agent,
        session_service=InMemorySessionService(),
    )

    run_sequential_agent(
        root_agent_runner,
        input_text="start",
    )
