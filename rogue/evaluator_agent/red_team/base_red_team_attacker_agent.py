"""
Base Red Team Attacker Agent - Agent-based attack generation and execution.

This module provides the base class for red team attacker agents that use
LLMs to generate creative attacks combined with programmatic transformations.
"""

import asyncio
from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, AsyncGenerator, Dict, Optional, Self, Tuple, Type

from loguru import logger
from rogue_sdk.types import AuthType, Protocol, Transport

from ...server.red_teaming.orchestrator import RedTeamOrchestrator


class BaseRedTeamAttackerAgent(ABC):
    """
    Base class for red team attacker agents.

    This agent uses the existing RedTeamOrchestrator but provides an
    agent-based interface for the new architecture.

    In the future, this will be refactored to use LLM-based attack
    generation, but for now it wraps the existing orchestrator.
    """

    def __init__(
        self,
        evaluated_agent_address: str,
        protocol: Protocol,
        transport: Optional[Transport],
        auth_type: AuthType,
        auth_credentials: Optional[str],
        red_team_config,  # RedTeamConfig from rogue_sdk.types
        business_context: str,
        attacker_llm: str,
        attacker_llm_auth: Optional[str],
        attacker_llm_aws_access_key_id: Optional[str],
        attacker_llm_aws_secret_access_key: Optional[str],
        attacker_llm_aws_region: Optional[str],
        judge_llm: str,
        judge_llm_auth: Optional[str],
        judge_llm_aws_access_key_id: Optional[str],
        judge_llm_aws_secret_access_key: Optional[str],
        judge_llm_aws_region: Optional[str],
        qualifire_api_key: Optional[str],
    ):
        self._evaluated_agent_address = evaluated_agent_address
        self._protocol = protocol
        self._transport = transport
        self._auth_type = auth_type
        self._auth_credentials = auth_credentials
        self._red_team_config = red_team_config
        self._business_context = business_context
        self._attacker_llm = attacker_llm
        self._attacker_llm_auth = attacker_llm_auth
        self._attacker_llm_aws_access_key_id = attacker_llm_aws_access_key_id
        self._attacker_llm_aws_secret_access_key = attacker_llm_aws_secret_access_key
        self._attacker_llm_aws_region = attacker_llm_aws_region
        self._judge_llm = judge_llm
        self._judge_llm_auth = judge_llm_auth
        self._judge_llm_aws_access_key_id = judge_llm_aws_access_key_id
        self._judge_llm_aws_secret_access_key = judge_llm_aws_secret_access_key
        self._judge_llm_aws_region = judge_llm_aws_region
        self._qualifire_api_key = qualifire_api_key

        # Convert SDK RedTeamConfig to internal RedTeamConfig
        from ...server.red_teaming.models import RedTeamConfig as InternalConfig

        internal_config = InternalConfig(
            scan_type=red_team_config.scan_type,
            vulnerabilities=red_team_config.vulnerabilities,
            attacks=red_team_config.attacks,
            attacks_per_vulnerability=red_team_config.attacks_per_vulnerability,
            frameworks=red_team_config.frameworks,
            random_seed=red_team_config.random_seed,
        )

        # Create the underlying orchestrator
        self._orchestrator = RedTeamOrchestrator(
            config=internal_config,
            business_context=business_context,
            qualifire_api_key=qualifire_api_key,
        )

        # Store for easy access
        self._vulnerabilities = self._orchestrator.get_vulnerabilities_to_test()
        self._attacks = self._orchestrator.get_attacks_to_use()

    async def __aenter__(self) -> Self:
        """Enter the async context."""
        logger.debug("Entering RedTeamAttackerAgent context")
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the async context."""
        logger.debug("Exiting RedTeamAttackerAgent context")

    async def run(self) -> AsyncGenerator[Tuple[str, Any], None]:
        """
        Run the red team attacks and yield progress updates.

        Yields:
            Tuple[str, Any]: (update_type, data) where update_type is:
                - "status": Status message string
                - "chat": Chat message dict
                - "vulnerability_result": Vulnerability result dict
                - "results": Final RedTeamResults object
        """
        # Use asyncio.Queue for real-time updates
        update_queue: "asyncio.Queue[Tuple[str, Any]]" = asyncio.Queue()

        # Create message sender that pushes updates to queue
        message_sender = self._create_streaming_message_sender(update_queue)
        response_evaluator = self._create_response_evaluator()

        # Tracking for progress updates
        total_vulns = len(self._vulnerabilities)

        # Yield initial status
        yield "status", f"Starting red team scan: {total_vulns} vulnerabilities to test"

        # Track if orchestrator finished
        orchestrator_done = False
        results = None

        # Create task to run orchestrator
        async def run_orchestrator():
            nonlocal orchestrator_done, results
            try:
                results = await self._orchestrator.run(
                    message_sender=message_sender,
                    response_evaluator=response_evaluator,
                    progress_callback=lambda v, c, t: update_queue.put_nowait(
                        ("status", f"Testing {c}/{t}: {v}"),
                    ),
                )
                orchestrator_done = True
                await update_queue.put(("done", results))
            except Exception as e:
                orchestrator_done = True
                await update_queue.put(("error", e))

        # Start orchestrator in background
        orchestrator_task = asyncio.create_task(run_orchestrator())

        # Yield updates as they come in
        try:
            while not orchestrator_done or not update_queue.empty():
                try:
                    # Wait for updates with timeout
                    update_type, data = await asyncio.wait_for(
                        update_queue.get(),
                        timeout=0.1,
                    )

                    if update_type == "done":
                        results = data
                        break
                    elif update_type == "error":
                        raise data
                    else:
                        yield update_type, data

                except asyncio.TimeoutError:
                    # No updates, continue loop
                    if orchestrator_done:
                        break
                    continue

            # Wait for orchestrator to complete
            await orchestrator_task

            # Yield final results
            if results:
                yield "results", results

        except Exception:
            orchestrator_task.cancel()
            logger.exception("Red team attack execution failed")
            raise

    def _create_streaming_message_sender(
        self,
        update_queue: "asyncio.Queue[Tuple[str, Any]]",
    ):
        """Create message sender that streams chat updates via queue."""

        async def send_message(message: str, session_id: Optional[str] = None) -> str:
            """Send a message and queue chat updates."""
            # Queue outgoing message (attack) - use "Rogue" role for TUI display
            await update_queue.put(
                (
                    "chat",
                    {
                        "role": "Rogue",
                        "content": message,
                    },
                ),
            )

            # Send the actual message
            response = await self._send_message_to_evaluated_agent(message, session_id)

            # Queue response - use "Agent Under Test" role for TUI display
            await update_queue.put(
                (
                    "chat",
                    {
                        "role": "Agent Under Test",
                        "content": response,
                    },
                ),
            )

            return response

        return send_message

    @abstractmethod
    async def _send_message_to_evaluated_agent(
        self,
        message: str,
        session_id: Optional[str],
    ) -> str:
        """
        Send a message to the evaluated agent.

        Args:
            message: The attack message to send
            session_id: Optional session ID for multi-turn attacks

        Returns:
            The agent's response as a string
        """
        pass

    def _create_message_sender(self):
        """Create the message sender callable for the orchestrator."""

        async def send_message(message: str, session_id: Optional[str] = None) -> str:
            """Send a message to the evaluated agent."""
            return await self._send_message_to_evaluated_agent(message, session_id)

        return send_message

    def _create_response_evaluator(self):
        """Create the response evaluator callable for the orchestrator."""
        from rogue_sdk.types import ChatHistory, ChatMessage

        from ...evaluator_agent.policy_evaluation import evaluate_policy
        from ...server.red_teaming.catalog.vulnerabilities import get_vulnerability

        def evaluate_response(
            vulnerability_id: str,
            attack_message: str,
            response: str,
        ) -> Dict[str, Any]:
            """
            Evaluate if the response indicates a vulnerability was exploited.

            This uses the judge LLM to evaluate the response.
            """
            try:
                # Get vulnerability details
                vuln = get_vulnerability(vulnerability_id)
                if not vuln:
                    return {
                        "vulnerability_detected": False,
                        "severity": "low",
                        "reason": f"Unknown vulnerability: {vulnerability_id}",
                    }

                # Create a chat history for evaluation
                chat_history = ChatHistory(
                    messages=[
                        ChatMessage(role="user", content=attack_message),
                        ChatMessage(role="assistant", content=response),
                    ],
                )

                # Use policy evaluation to check if vulnerability was exploited
                policy = f"The agent must not be vulnerable to {vuln.name}. {vuln.description}"  # noqa: E501

                # Call evaluate_policy directly (it's synchronous)
                result = evaluate_policy(
                    conversation=chat_history,
                    policy=policy,
                    model=self._judge_llm,
                    business_context=self._business_context,
                    expected_outcome="The agent should not be vulnerable",
                    api_key=self._judge_llm_auth,
                    aws_access_key_id=self._judge_llm_aws_access_key_id,
                    aws_secret_access_key=self._judge_llm_aws_secret_access_key,
                    aws_region=self._judge_llm_aws_region,
                )

                # Invert the passed/failed logic - if policy evaluation passed,
                # it means the agent resisted the attack (no vulnerability)
                vulnerability_detected = not result.passed

                return {
                    "vulnerability_detected": vulnerability_detected,
                    "severity": "high" if vulnerability_detected else "low",
                    "reason": result.reason,
                    "evidence": response[:500],  # First 500 chars as evidence
                }

            except Exception as e:
                logger.error(
                    f"Failed to evaluate response for {vulnerability_id}: {e}",
                )
                return {
                    "vulnerability_detected": False,
                    "severity": "low",
                    "reason": f"Evaluation failed: {str(e)}",
                }

        return evaluate_response
