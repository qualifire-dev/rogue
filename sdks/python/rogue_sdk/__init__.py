"""
Rogue Agent Evaluator Python SDK

A comprehensive Python SDK for interacting with the Rogue Agent Evaluator API.

Example:
    ```python
    import asyncio
    from rogue_sdk import RogueSDK, RogueClientConfig, AuthType, ScenarioType

    async def main():
        config = RogueClientConfig(base_url="http://localhost:8000")

        async with RogueSDK(config) as client:
            # Quick evaluation
            result = await client.quick_evaluate(
                agent_url="http://localhost:3000",
                scenarios=["The agent should be polite", "No discounts allowed"]
            )
            print(f"Evaluation result: {result.status}")

            # Evaluation with real-time updates
            job = await client.run_evaluation_with_updates(
                request={
                    "agent_config": {
                        "evaluated_agent_url": "http://localhost:3000",
                        "evaluated_agent_auth_type": AuthType.NO_AUTH,
                        "judge_llm": "openai/gpt-4o-mini"
                    },
                    "scenarios": [{
                        "scenario": "Test scenario",
                        "scenario_type": ScenarioType.POLICY
                    }]
                },
                on_update=lambda job: print(f"Status: {job.status}"),
                on_chat=lambda chat: print(f"Chat: {chat}")
            )

    asyncio.run(main())
    ```
"""

# HTTP and WebSocket clients
from .client import RogueHttpClient

# Main SDK class
from .sdk import RogueSDK

# All types
from .types import *
from . import types

from .websocket import RogueWebSocketClient

# Version
__version__ = "1.0.0"

# Default export
__all__ = [
    "RogueSDK",
    "RogueHttpClient",
    "RogueWebSocketClient",
    "RogueClientConfig",
    "EvaluationRequest",
    "EvaluationResponse",
    "EvaluationJob",
    "EvaluationResult",
    "AgentConfig",
    "Scenario",
    "AuthType",
    "ScenarioType",
    "EvaluationStatus",
    "HealthResponse",
    "JobListResponse",
    "WebSocketMessage",
    "StructuredSummary",
    "SummaryGenerationRequest",
    "SummaryGenerationResponse",
    "ReportSummaryResponse",
    "ReportSummaryRequest",
]
