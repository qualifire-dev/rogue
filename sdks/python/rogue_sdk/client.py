"""
HTTP Client for Rogue Agent Evaluator API.
"""

import asyncio
from typing import Optional

import backoff
import httpx

from .types import (
    EvaluationJob,
    EvaluationRequest,
    EvaluationResponse,
    EvaluationStatus,
    GetConversationResponse,
    HealthResponse,
    JobListResponse,
    RogueClientConfig,
    SendMessageResponse,
    StartInterviewResponse,
)


class RogueHttpClient:
    """HTTP client for Rogue Agent Evaluator API."""

    def __init__(self, config: RogueClientConfig):
        self.base_url = str(config.base_url).rstrip("/")
        self.api_key = config.api_key
        self.timeout = config.timeout
        self.retries = config.retries

        # Create HTTP client
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url, headers=headers, timeout=self.timeout
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make HTTP request with retry logic."""

        @backoff.on_exception(
            backoff.expo,
            Exception,
            max_time=self.timeout,
            max_tries=self.retries,
        )
        async def request():
            """Make HTTP request."""
            response = await self._client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response.json()

        return await request()

    async def health(self) -> HealthResponse:
        """Check server health."""
        data = await self._request("GET", "/api/v1/health")
        return HealthResponse(**data)

    async def create_evaluation(self, request: EvaluationRequest) -> EvaluationResponse:
        """Create and start a new evaluation job."""
        data = await self._request(
            "POST",
            "/api/v1/evaluations",
            json=request.model_dump(mode="json"),
        )
        return EvaluationResponse(**data)

    async def get_evaluation(self, job_id: str) -> EvaluationJob:
        """Get evaluation job by ID."""
        data = await self._request("GET", f"/api/v1/evaluations/{job_id}")
        return EvaluationJob(**data)

    async def list_evaluations(
        self,
        status: Optional[EvaluationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> JobListResponse:
        """List evaluation jobs."""
        params = {"limit": str(limit), "offset": str(offset)}
        if status:
            params["status"] = status.value

        data = await self._request("GET", "/api/v1/evaluations", params=params)
        return JobListResponse(**data)

    async def cancel_evaluation(self, job_id: str) -> dict:
        """Cancel evaluation job."""
        return await self._request("DELETE", f"/api/v1/evaluations/{job_id}")

    async def generate_scenarios(
        self,
        business_context: str,
        model: str,
        api_key: Optional[str] = None,
        count: int = 10,
    ) -> dict:
        """Generate scenarios via API."""
        data = {
            "business_context": business_context,
            "model": model,
            "count": count,
        }
        if api_key:
            data["api_key"] = api_key

        return await self._request("POST", "/api/v1/llm/scenarios", json=data)

    async def generate_summary(
        self,
        results: dict,
        model: str,
        api_key: Optional[str] = None,
    ) -> dict:
        """Generate summary via API."""
        data = {
            "results": results,
            "model": model,
        }
        if api_key:
            data["api_key"] = api_key

        return await self._request("POST", "/api/v1/llm/summary", json=data)

    async def start_interview(
        self,
        model: str = "openai/gpt-4o-mini",
        api_key: Optional[str] = None,
    ) -> StartInterviewResponse:
        """Start a new interview session."""
        data = {"model": model}
        if api_key:
            data["api_key"] = api_key

        response = await self._request(
            "POST",
            "/api/v1/interview/start",
            json=data,
        )

        return StartInterviewResponse(**response)

    async def send_interview_message(
        self,
        session_id: str,
        message: str,
    ) -> SendMessageResponse:
        """Send a message in an interview session."""
        data = {"session_id": session_id, "message": message}
        response = await self._request(
            "POST",
            "/api/v1/interview/message",
            json=data,
        )
        return SendMessageResponse(**response)

    async def get_interview_conversation(
        self, session_id: str
    ) -> GetConversationResponse:
        """Get the full conversation for an interview session."""
        response = await self._request(
            "GET", f"/api/v1/interview/conversation/{session_id}"
        )
        return GetConversationResponse(**response)

    async def end_interview(self, session_id: str) -> None:
        """End an interview session."""
        await self._request("DELETE", f"/api/v1/interview/session/{session_id}")

    async def wait_for_evaluation(
        self,
        job_id: str,
        poll_interval: float = 1.0,
        max_wait_time: float = 3000.0,
    ) -> EvaluationJob:
        """Wait for evaluation to complete with polling."""
        start_time = asyncio.get_event_loop().time()

        while True:
            job = await self.get_evaluation(job_id)

            if job.status in [
                EvaluationStatus.COMPLETED,
                EvaluationStatus.FAILED,
                EvaluationStatus.CANCELLED,
            ]:
                return job

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= max_wait_time:
                raise TimeoutError(
                    f"Evaluation {job_id} did not complete within {max_wait_time}s"
                )

            await asyncio.sleep(poll_interval)
