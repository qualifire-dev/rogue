from types import TracebackType
from typing import Callable, Optional, Self, Type

from loguru import logger
from rogue_sdk.types import Protocol, Scenarios, Transport

from .base_evaluator_agent import BaseEvaluatorAgent


class MCPEvaluatorAgent(BaseEvaluatorAgent):
    def __init__(
        self,
        transport: Optional[Transport],
        evaluated_agent_address: str,
        judge_llm: str,
        scenarios: Scenarios,
        business_context: Optional[str],
        headers: Optional[dict[str, str]] = None,
        judge_llm_auth: Optional[str] = None,
        debug: bool = False,
        deep_test_mode: bool = False,
        chat_update_callback: Optional[Callable[[dict], None]] = None,
        *args,
        **kwargs,
    ):
        from fastmcp import Client
        from fastmcp.client import SSETransport, StreamableHttpTransport

        super().__init__(
            evaluated_agent_address=evaluated_agent_address,
            protocol=Protocol.MCP,
            transport=transport,
            judge_llm=judge_llm,
            scenarios=scenarios,
            business_context=business_context,
            headers=headers,
            judge_llm_auth=judge_llm_auth,
            debug=debug,
            deep_test_mode=deep_test_mode,
            chat_update_callback=chat_update_callback,
        )

        self._client: Client[SSETransport | StreamableHttpTransport]

        if self._transport == Transport.SSE:
            self._client = Client[SSETransport](
                transport=SSETransport(
                    url=evaluated_agent_address,
                    headers=headers,
                ),
            )
        elif self._transport == Transport.STREAMABLE_HTTP:
            self._client = Client[StreamableHttpTransport](
                transport=StreamableHttpTransport(
                    url=evaluated_agent_address,
                    headers=headers,
                ),
            )
        else:
            raise ValueError(f"Unsupported transport for MCP: {self._transport}")

    async def __aenter__(self) -> Self:
        await self._client.__aenter__()
        return await super().__aenter__()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        await super().__aexit__(exc_type, exc_value, traceback)
        await self._client.__aexit__(exc_type, exc_value, traceback)

    async def _send_message_to_evaluated_agent(
        self,
        context_id: str,
        message: str,
    ) -> dict[str, str]:
        logger.info(
            "🔗 Making MCP call to evaluated agent",
            extra={
                "message": message[:100] + "..." if len(message) > 100 else message,
                "context_id": context_id,
                "agent_url": self._evaluated_agent_address,
                "transport": self._transport.value,
            },
        )

        self._add_message_to_chat_history(context_id, "user", message)
        response = await self._invoke_mcp_agent(message)
        if not response or not response.get("response"):
            logger.debug(
                "_send_message_to_evaluated_agent - no response",
                extra={"protocol": "mcp"},
            )
            return {"response": ""}

        self._add_message_to_chat_history(
            context_id,
            "assistant",
            response.get(
                "response",
                "Not a text response",
            ),
        )

        return response

    async def _invoke_mcp_agent(self, message: str) -> dict[str, str]:
        try:
            tool_result = await self._client.call_tool(
                name="send_message",
                arguments={
                    "message": message,
                },
            )

            text_response = ""
            for part in tool_result.content:
                if part.type != "text":
                    logger.warning(
                        "Received non-text part in tool result",
                        extra={"type": part.type},
                    )
                    continue

                text_response += part.text

            return {"response": text_response}
        except Exception as e:
            logger.exception(
                "Error while sending message to evaluated agent using mcp",
                extra={
                    "protocol": "mcp",
                    "agent_url": self._evaluated_agent_address,
                    "transport": self._transport.value,
                    "message": message[:100] + "..." if len(message) > 100 else message,
                },
            )
            return {
                "response": "",
                "error": str(e),
            }
