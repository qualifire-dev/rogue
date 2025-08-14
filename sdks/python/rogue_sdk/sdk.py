"""
Main Rogue Agent Evaluator Python SDK.

Combines HTTP client and WebSocket client for complete functionality.
"""

import asyncio
from typing import Callable, Optional

from loguru import logger
from pydantic import HttpUrl

from .client import RogueHttpClient
from .types import (
    AgentConfig,
    AuthType,
    EvaluationJob,
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResults,
    EvaluationStatus,
    HealthResponse,
    InterviewSession,
    JobListResponse,
    RogueClientConfig,
    Scenarios,
    SendMessageResponse,
    WebSocketEventType,
)
from .websocket import RogueWebSocketClient


class RogueSDK:
    """Main SDK class for Rogue Agent Evaluator."""

    def __init__(self, config: RogueClientConfig):
        self.config = config
        self.http_client = RogueHttpClient(config)
        self.ws_client: Optional[RogueWebSocketClient] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close all connections."""
        if self.ws_client:
            await self.ws_client.disconnect()
        await self.http_client.close()

    # HTTP Client Methods

    async def health(self) -> HealthResponse:
        """Check server health."""
        return await self.http_client.health()

    async def create_evaluation(self, request: EvaluationRequest) -> EvaluationResponse:
        """Create and start an evaluation job."""
        return await self.http_client.create_evaluation(request)

    async def get_evaluation(self, job_id: str) -> EvaluationJob:
        """Get evaluation job details."""
        return await self.http_client.get_evaluation(job_id)

    async def list_evaluations(
        self,
        status: Optional[EvaluationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> JobListResponse:
        """List evaluation jobs."""
        return await self.http_client.list_evaluations(status, limit, offset)

    async def cancel_evaluation(self, job_id: str) -> dict:
        """Cancel evaluation job."""
        return await self.http_client.cancel_evaluation(job_id)

    async def wait_for_evaluation(
        self, job_id: str, poll_interval: float = 2.0, max_wait_time: float = 300.0
    ) -> EvaluationJob:
        """Wait for evaluation to complete (polling)."""
        return await self.http_client.wait_for_evaluation(
            job_id, poll_interval, max_wait_time
        )

    # WebSocket Methods

    async def connect_websocket(self, job_id: str) -> None:
        """Connect to WebSocket for real-time updates."""
        if self.ws_client:
            await self.ws_client.disconnect()

        self.ws_client = RogueWebSocketClient(str(self.config.base_url), job_id)
        await self.ws_client.connect()

    async def disconnect_websocket(self) -> None:
        """Disconnect WebSocket."""
        if self.ws_client:
            await self.ws_client.disconnect()
            self.ws_client = None

    def on_websocket_event(self, event: WebSocketEventType, handler: Callable) -> None:
        """Add WebSocket event handler."""
        if not self.ws_client:
            raise RuntimeError(
                "WebSocket not connected. Call connect_websocket() first."
            )
        self.ws_client.on(event, handler)

    def off_websocket_event(self, event: WebSocketEventType, handler: Callable) -> None:
        """Remove WebSocket event handler."""
        if self.ws_client:
            self.ws_client.off(event, handler)

    @property
    def is_websocket_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.ws_client.is_connected if self.ws_client else False

    # High-level convenience methods

    async def run_evaluation_with_updates(
        self,
        request: EvaluationRequest,
        on_update: Optional[Callable[[EvaluationJob], None]] = None,
        on_chat: Optional[Callable[[dict], None]] = None,
        timeout: float = 600.0,
    ) -> EvaluationJob:
        """Run evaluation with real-time updates."""
        # Create evaluation
        response = await self.create_evaluation(request)
        job_id = response.job_id

        # Set up completion tracking
        result_future: asyncio.Future[EvaluationJob] = asyncio.Future()

        def handle_job_update(event, data):
            # Don't try to create EvaluationJob from partial WebSocket data
            # Just pass the status update data to the callback
            if on_update:
                # Create a simple status update object instead of full EvaluationJob
                status_update = {
                    "job_id": job_id,
                    "status": data.get("status"),
                    "progress": data.get("progress", 0.0),
                    "error_message": data.get("error_message"),
                }
                # Call the callback with a simple dict instead of EvaluationJob
                try:
                    on_update(status_update)
                except Exception as e:
                    logger.warning(f"Status update callback failed: {e}")

            # Check if job is complete
            status = data.get("status")
            if status in ["completed", "failed", "cancelled"]:
                if not result_future.done():
                    # Get the full job when complete instead of using partial
                    # WebSocket data
                    async def get_final_job():
                        try:
                            return await self.get_evaluation(job_id)
                        except Exception:
                            logger.exception("Failed to get final job")
                            # Return None to indicate failure
                            return None

                    def handle_final_job_result(task):
                        if result_future.done():
                            return
                        try:
                            result = task.result()
                            if result:
                                result_future.set_result(result)
                            else:
                                result_future.set_exception(
                                    Exception("Failed to retrieve final job result")
                                )
                        except Exception as e:
                            result_future.set_exception(e)

                    task = asyncio.create_task(get_final_job())
                    task.add_done_callback(handle_final_job_result)

        def handle_chat_update(event, data):
            if on_chat:
                on_chat(data)

        def handle_error(event, data):
            if not result_future.done():
                result_future.set_exception(
                    Exception(f"WebSocket error: {data.get('error')}")
                )

        # Connect WebSocket for updates
        await self.connect_websocket(job_id)

        # Set up event handlers
        self.on_websocket_event("job_update", handle_job_update)
        self.on_websocket_event("error", handle_error)
        if on_chat:
            self.on_websocket_event("chat_update", handle_chat_update)

        try:
            # Wait for completion or timeout
            result = await asyncio.wait_for(result_future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Evaluation {job_id} did not complete within {timeout}s"
            )
        finally:
            await self.disconnect_websocket()

    async def run_evaluation(
        self,
        agent_url: str,
        scenarios: Scenarios,
        business_context: str,
        judge_model: str = "openai/gpt-4o-mini",
        auth_type: AuthType = AuthType.NO_AUTH,
        auth_credentials: Optional[str] = None,
        deep_test: bool = False,
        timeout: float = 600.0,
    ) -> EvaluationJob:
        """Quick evaluation helper."""
        agent_config = AgentConfig(
            agent_url=HttpUrl(agent_url),
            auth_type=auth_type,
            auth_credentials=auth_credentials,
            judge_llm=judge_model,
            deep_test_mode=deep_test,
            interview_mode=True,
            parallel_runs=1,
            business_context=business_context,
        )

        request = EvaluationRequest(
            agent_config=agent_config,
            scenarios=scenarios.scenarios,
            max_retries=3,
            timeout_seconds=int(timeout),
        )

        response = await self.create_evaluation(request)
        return await self.wait_for_evaluation(response.job_id)

    async def generate_scenarios(
        self,
        business_context: str,
        model: str = "openai/gpt-4o-mini",
        api_key: Optional[str] = None,
        count: int = 10,
    ) -> "Scenarios":
        """Generate test scenarios based on business context."""
        from .types import Scenarios

        response_data = await self.http_client.generate_scenarios(
            business_context=business_context,
            model=model,
            api_key=api_key,
            count=count,
        )

        return Scenarios.model_validate(response_data["scenarios"])

    async def generate_summary(
        self,
        results: "EvaluationResults",
        model: str = "openai/gpt-4o-mini",
        api_key: Optional[str] = None,
    ) -> str:
        """Generate evaluation summary from results."""
        response_data = await self.http_client.generate_summary(
            results=results.model_dump(),
            model=model,
            api_key=api_key,
        )

        return response_data["summary"]

    async def start_interview(
        self,
        model: str = "openai/gpt-4o-mini",
        api_key: Optional[str] = None,
    ) -> InterviewSession:
        """Start a new interview session."""
        response_data = await self.http_client.start_interview(
            model=model,
            api_key=api_key,
        )

        return InterviewSession(
            session_id=response_data.session_id,
            messages=[],
            is_complete=False,
            message_count=0,
        )

    async def send_interview_message(
        self,
        session_id: str,
        message: str,
    ) -> SendMessageResponse:
        """
        Send a message in an interview session.

        Returns:
            tuple: (response, is_complete, message_count)
        """
        return await self.http_client.send_interview_message(
            session_id=session_id,
            message=message,
        )

    async def get_interview_conversation(self, session_id: str) -> InterviewSession:
        """Get the full conversation for an interview session."""
        response_data = await self.http_client.get_interview_conversation(session_id)

        return InterviewSession(
            session_id=response_data.session_id,
            messages=response_data.messages,
            is_complete=response_data.is_complete,
            message_count=response_data.message_count,
        )

    async def end_interview(self, session_id: str) -> None:
        """End an interview session."""
        await self.http_client.end_interview(session_id)
