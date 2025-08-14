"""
Core evaluation library - Clean API for agent evaluation
"""

import asyncio
from typing import Any, AsyncGenerator, Callable, Optional

from loguru import logger
from pydantic import HttpUrl
from rogue_sdk.types import (
    AgentConfig,
    AuthType,
    EvaluationResults,
    Scenario,
    Scenarios,
    ScenarioType,
)

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
        logger.info(
            "🚀 EvaluationLibrary.evaluate_agent starting",
            extra={
                "agent_url": str(agent_config.evaluated_agent_url),
                "scenario_count": len(scenarios.scenarios),
                "judge_llm": agent_config.judge_llm,
                "deep_test_mode": agent_config.deep_test_mode,
                "business_context_length": len(business_context),
                "has_progress_callback": progress_callback is not None,
            },
        )

        try:
            service = ScenarioEvaluationService(
                evaluated_agent_url=str(agent_config.evaluated_agent_url),
                evaluated_agent_auth_type=agent_config.evaluated_agent_auth_type,
                evaluated_agent_auth_credentials=(
                    agent_config.evaluated_agent_credentials
                ),
                judge_llm=agent_config.judge_llm,
                judge_llm_api_key=agent_config.judge_llm_api_key,
                scenarios=scenarios,
                business_context=business_context,
                deep_test_mode=agent_config.deep_test_mode,
            )

            logger.info("📋 ScenarioEvaluationService created successfully")

            results = None
            update_count = 0

            logger.info("🔄 Starting to iterate over scenario evaluation updates")

            async for update_type, data in service.evaluate_scenarios():
                update_count += 1
                logger.info(
                    f"📨 EvaluationLibrary received update #{update_count}",
                    extra={
                        "update_type": update_type,
                        "data_type": type(data).__name__,
                        "data_preview": str(data)[:100] if data else "None",
                    },
                )

                if progress_callback:
                    logger.debug(
                        f"📤 Calling progress_callback with update_type='{update_type}'"
                    )
                    try:
                        progress_callback(update_type, data)
                        logger.debug("✅ progress_callback completed successfully")
                    except Exception:
                        logger.exception("❌ progress_callback failed")

                if update_type == "done":
                    results = data
                    logger.info(
                        "✅ Evaluation completed with "
                        f"{len(results.results) if results and results.results else 0} "
                        "results"
                    )
                    break

            logger.info(
                (
                    "🏁 Finished iterating over updates. "
                    f"Total updates received: {update_count}"
                )
            )

            if not results:
                logger.error("❌ No results returned from evaluation")
                raise RuntimeError("Evaluation failed - no results returned")

            logger.info("🎉 EvaluationLibrary.evaluate_agent completed successfully")
            return results

        except Exception:
            logger.exception(
                "💥 EvaluationLibrary.evaluate_agent failed",
                extra={
                    "agent_url": str(agent_config.evaluated_agent_url),
                    "scenario_count": len(scenarios.scenarios),
                },
            )
            raise

    @staticmethod
    async def evaluate_agent_streaming(
        agent_config: AgentConfig,
        scenarios: Scenarios,
        business_context: str,
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
            evaluated_agent_url=str(agent_config.evaluated_agent_url),
            evaluated_agent_auth_type=agent_config.evaluated_agent_auth_type,
            evaluated_agent_auth_credentials=agent_config.evaluated_agent_credentials,
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

    # Convert string scenarios to Scenario objects
    scenario_objects = [
        Scenario(scenario=desc, scenario_type=ScenarioType.POLICY) for desc in scenarios
    ]
    scenarios_obj = Scenarios(scenarios=scenario_objects)

    # Create agent config
    agent_config = AgentConfig(
        evaluated_agent_url=HttpUrl(agent_url),
        evaluated_agent_auth_type=AuthType(auth_type),
        evaluated_agent_credentials=auth_credentials,
        judge_llm=judge_llm,
        judge_llm_api_key=judge_llm_api_key,
    )

    return await EvaluationLibrary.evaluate_agent(
        agent_config=agent_config,
        scenarios=scenarios_obj,
    )
