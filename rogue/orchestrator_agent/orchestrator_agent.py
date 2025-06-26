from google.adk.agents import SequentialAgent, BaseAgent


class OrchestratorAgentFactory:
    def __init__(
        self,
        scenario_generation_agent: BaseAgent,
        evaluator_agent: BaseAgent,
        report_generation_agent: BaseAgent,
    ):
        self._agents = [
            scenario_generation_agent,  # interviews and generates scenarios
            evaluator_agent,  # runs scenarios on evaluated agent
            report_generation_agent,  # generates report from evaluator results
        ]

    def create_agent(self) -> SequentialAgent:
        return SequentialAgent(
            name="Qualifire agent-evaluator orchestrator",
            sub_agents=self._agents,
            description="Orchestrates the evaluation of agents",
        )
