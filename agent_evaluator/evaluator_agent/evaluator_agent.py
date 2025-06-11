from typing import Any
from uuid import uuid4

from a2a.client import A2ACardResolver
from a2a.types import (
    Message,
    MessageSendParams,
    Role,
    Part,
    TextPart,
)
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from httpx import AsyncClient
from loguru import logger

from ..common.agent_model_wrapper import get_llm_from_model
from ..common.remote_agent_connection import RemoteAgentConnections

AGENT_INSTRUCTIONS = """
"""  # noqa: E501


class EvaluatorAgentFactory:
    def __init__(
        self,
        http_client: AsyncClient,
        evaluated_agent_address: str,
        model: str,
    ) -> None:
        self._http_client = http_client
        self._evaluated_agent_address = evaluated_agent_address
        self._model = model
        self._evaluation_logs: list[dict[str, Any]] = []
        self.__evaluated_agent_client: RemoteAgentConnections | None = None
        self._test_case_context_ids: dict[str, str] = {}

    async def _get_evaluated_agent(self) -> RemoteAgentConnections:
        logger.debug("_get_evaluated_agent - enter")
        if self.__evaluated_agent_client is None:
            card_resolver = A2ACardResolver(
                self._http_client,
                self._evaluated_agent_address,
            )
            card = await card_resolver.get_agent_card()
            self.__evaluated_agent_client = RemoteAgentConnections(
                self._http_client,
                card,
            )

        return self.__evaluated_agent_client

    def create_agent(self) -> LlmAgent:
        return LlmAgent(
            name="qualifire_agent_evaluator",
            description="An agent that runs amd evaluates test scenarios on other agents",
            model=get_llm_from_model(self._model),
            instruction=AGENT_INSTRUCTIONS,
            tools=[
                FunctionTool(func=self._get_evaluated_agent_card),
                FunctionTool(func=self._log_evaluation),
                FunctionTool(func=self._send_prompt_to_evaluated_agent),
                FunctionTool(func=self._get_context_id_for_test_case),
            ],
        )

    async def _get_evaluated_agent_card(self) -> str:
        """
        Get evaluated agent card.
        :return: The evaluated agent card.
        """
        agent_client = await self._get_evaluated_agent()
        return agent_client.get_agent().model_dump_json()

    def _log_evaluation(
        self,
        scenario: str,
        test_case: str,
        prompt: str,
        response: str,
        evaluation: bool,
        reason: str,
    ) -> None:
        """
        Logs the evaluation of the given scenario and test case.
        :param scenario: The scenario being evaluated.
        :param test_case: The specific test case in the scenario.
        :param prompt: The prompt sent to the evaluated agent.
        :param response: The response from the evaluated agent.
        :param evaluation: The evaluation result.
        :param reason: The reason for the evaluation.
        :return: None
        """
        logger.debug(
            "_log_evaluation - enter",
            extra={
                "scenario": scenario,
                "test_case": test_case,
                "prompt": prompt,
                "response": response,
                "evaluation": evaluation,
                "reason": reason,
            },
        )
        self._evaluation_logs.append(
            {
                "scenario": scenario,
                "test_case": test_case,
                "prompt": prompt,
                "response": response,
                "evaluation": evaluation,
                "reason": reason,
            },
        )

    async def _send_prompt_to_evaluated_agent(
        self,
        prompt: str,
        context_id: str,
    ) -> str | None:
        """
        Sends a message to the evaluated agent.
        :param prompt: The message content to send.
        :param context_id: The context ID of the message.
            Generate a random context_id for each conversation.
            For multi-turn conversations, use the same context_id for each turn.
        :return: The response from the evaluated agent.
        """
        logger.debug(
            "_send_prompt_to_evaluated_agent - enter",
            extra={
                "prompt": prompt,
                "context_id": context_id,
            },
        )
        agent_client = await self._get_evaluated_agent()
        response = await agent_client.send_message(
            MessageSendParams(
                message=Message(
                    contextId=context_id,
                    messageId=uuid4().hex,
                    role=Role.user,
                    parts=[
                        Part(
                            root=TextPart(
                                text=prompt,
                            )
                        ),
                    ],
                ),
            ),
        )

        if not response:
            logger.debug("_send_prompt_to_evaluated_agent - no response")
            return None

        logger.debug(
            "_send_prompt_to_evaluated_agent - response",
            extra={"response": response.model_dump_json()},
        )
        return response.model_dump_json()

    async def _get_context_id_for_test_case(
        self,
        test_case_id: str,
    ) -> str:
        """
        Generates a unique context_id for the given test case.
        :param test_case_id: The test case ID.
        :return: The context ID for the test case.
        """
        context_id = self._test_case_context_ids.get(test_case_id)
        if context_id is None:
            context_id = uuid4().hex
            self._test_case_context_ids[test_case_id] = context_id
        return context_id
