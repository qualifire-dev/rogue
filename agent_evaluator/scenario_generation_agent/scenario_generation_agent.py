from a2a.types import AgentCard
from google.adk.agents import LlmAgent

from ..common.agent_model_wrapper import get_llm_from_model
from ..models.scenario import Scenarios


class ScenarioGenerationAgentFactory:
    def create_agent(self, agent_card: AgentCard, model: str):
        # TODO: dror
        # This is a placeholder for now
        return LlmAgent(
            name="Scenario Generation Agent",
            description="TBD",
            model=get_llm_from_model(model),
            instruction="""You are an agent designed to return this """,
            output_schema=Scenarios,
            output_key="scenarios",
        )
