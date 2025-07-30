"""
Core evaluation library - Clean API for agent evaluation
"""

import asyncio
from typing import AsyncGenerator, Callable, Optional, Any

from ..models.config import AgentConfig
from ..models.scenario import Scenarios
from ..models.evaluation_result import EvaluationResults
from .scenario_evaluation_service import ScenarioEvaluationService


class EvaluationLibrary:
    """
    Clean library interface for agent evaluation.

    This is the core evaluation engine that can be used by:
    - FastAPI server
    - CLI interface
    - UI components
    - External integrations
    """

    @staticmethod
    async def evaluate_agent(
        agent_config: AgentConfig,
        scenarios: Scenarios,
        business_context: str = "The agent provides customer service.",
        progress_callback: Optional[Callable[[str, Any], None]] = None,
    ) -> EvaluationResults:
        """
        Evaluate an agent against scenarios.

        Args:
            agent_config: Configuration for the agent to evaluate
            scenarios: Scenarios to test against
            business_context: Business context for evaluation
            progress_callback: Optional callback for progress updates

        Returns:
            EvaluationResults containing all evaluation data
        """
        service = ScenarioEvaluationService(
            evaluated_agent_url=str(agent_config.agent_url),
            evaluated_agent_auth_type=agent_config.auth_type,
            evaluated_agent_auth_credentials=agent_config.auth_credentials,
            judge_llm=agent_config.judge_llm,
            judge_llm_api_key=agent_config.judge_llm_api_key,
            scenarios=scenarios,
            business_context=business_context,
            deep_test_mode=agent_config.deep_test_mode,
        )

        results = None
        async for update_type, data in service.evaluate_scenarios():
            if progress_callback:
                progress_callback(update_type, data)

            if update_type == "done":
                results = data
                break

        if not results:
            raise RuntimeError("Evaluation failed - no results returned")

        return results

    @staticmethod
    async def evaluate_agent_streaming(
        agent_config: AgentConfig,
        scenarios: Scenarios,
        business_context: str = "The agent provides customer service.",
    ) -> AsyncGenerator[tuple[str, Any], None]:
        """
        Evaluate an agent with streaming updates.

        Args:
            agent_config: Configuration for the agent to evaluate
            scenarios: Scenarios to test against
            business_context: Business context for evaluation

        Yields:
            Tuple of (update_type, data) for real-time updates
        """
        service = ScenarioEvaluationService(
            evaluated_agent_url=str(agent_config.agent_url),
            evaluated_agent_auth_type=agent_config.auth_type,
            evaluated_agent_auth_credentials=agent_config.auth_credentials,
            judge_llm=agent_config.judge_llm,
            judge_llm_api_key=agent_config.judge_llm_api_key,
            scenarios=scenarios,
            business_context=business_context,
            deep_test_mode=agent_config.deep_test_mode,
        )

        async for update_type, data in service.evaluate_scenarios():
            yield update_type, data

    @staticmethod
    def evaluate_agent_sync(
        agent_config: AgentConfig,
        scenarios: Scenarios,
        business_context: str = "The agent provides customer service.",
        progress_callback: Optional[Callable[[str, Any], None]] = None,
    ) -> EvaluationResults:
        """
        Synchronous wrapper for agent evaluation.

        Args:
            agent_config: Configuration for the agent to evaluate
            scenarios: Scenarios to test against
            business_context: Business context for evaluation
            progress_callback: Optional callback for progress updates

        Returns:
            EvaluationResults containing all evaluation data
        """
        return asyncio.run(
            EvaluationLibrary.evaluate_agent(
                agent_config=agent_config,
                scenarios=scenarios,
                business_context=business_context,
                progress_callback=progress_callback,
            )
        )


# Convenience functions for common use cases
async def quick_evaluate(
    agent_url: str,
    scenarios: list[str],
    judge_llm: str = "openai/gpt-4o-mini",
    auth_type: str = "no_auth",
    auth_credentials: Optional[str] = None,
    judge_llm_api_key: Optional[str] = None,
) -> EvaluationResults:
    """
    Quick evaluation with minimal configuration.

    Args:
        agent_url: URL of the agent to evaluate
        scenarios: List of scenario descriptions
        judge_llm: LLM model for evaluation
        auth_type: Authentication type
        auth_credentials: Authentication credentials
        judge_llm_api_key: API key for judge LLM

    Returns:
        EvaluationResults
    """
    from ..models.config import AuthType
    from ..models.scenario import Scenario, ScenarioType

    # Convert string scenarios to Scenario objects
    scenario_objects = [
        Scenario(scenario=desc, scenario_type=ScenarioType.POLICY) for desc in scenarios
    ]
    scenarios_obj = Scenarios(scenarios=scenario_objects)

    # Create agent config
    from pydantic import HttpUrl

    agent_config = AgentConfig(
        evaluated_agent_url=HttpUrl(agent_url),
        evaluated_agent_auth_type=AuthType(auth_type),
        evaluated_agent_credentials=auth_credentials,
        judge_llm_model=judge_llm,
        judge_llm_api_key=judge_llm_api_key,
    )

    return await EvaluationLibrary.evaluate_agent(
        agent_config=agent_config,
        scenarios=scenarios_obj,
    )
