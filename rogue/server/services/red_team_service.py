"""Red Team Service - Manages red team scan jobs."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from rogue_sdk.types import (
    EvaluationStatus,
    RedTeamJob,
    WebSocketEventType,
    WebSocketMessage,
)

from ...common.logging import get_logger, set_job_context
from ..core.red_team_orchestrator import RedTeamOrchestrator
from ..websocket.manager import get_websocket_manager

logger = get_logger(__name__)


class RedTeamService:
    """Service for managing red team scan jobs."""

    def __init__(self) -> None:
        self.jobs: Dict[str, RedTeamJob] = {}
        self.logger = get_logger(__name__)
        self.websocket_manager = get_websocket_manager()
        self._lock = asyncio.Lock()

    async def add_job(self, job: RedTeamJob):
        """Add a new red team job."""
        async with self._lock:
            self.jobs[job.job_id] = job

    async def get_job(self, job_id: str) -> Optional[RedTeamJob]:
        """Get a red team job by ID."""
        async with self._lock:
            return self.jobs.get(job_id)

    async def get_jobs(
        self,
        status: Optional[EvaluationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[RedTeamJob]:
        """Get a list of red team jobs with optional filtering."""
        async with self._lock:
            jobs = list(self.jobs.values())

        if status:
            jobs = [job for job in jobs if job.status == status]

        jobs.sort(key=lambda x: x.created_at, reverse=True)
        return jobs[offset : offset + limit]

    async def get_job_count(self, status: Optional[EvaluationStatus] = None) -> int:
        """Get the count of red team jobs with optional status filtering."""
        async with self._lock:
            if status:
                return len([job for job in self.jobs.values() if job.status == status])
            return len(self.jobs)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running or pending red team job."""
        job = await self.get_job(job_id)
        if not job:
            return False

        if job.status in [EvaluationStatus.PENDING, EvaluationStatus.RUNNING]:
            job.status = EvaluationStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            self._notify_job_update(job)

        return True

    async def run_job(self, job_id: str):
        """Run a red team scan job."""
        job = await self.get_job(job_id)
        if not job:
            return

        try:
            # Set job context for logging
            set_job_context(
                job_id=job_id,
                agent_url=str(job.request.evaluated_agent_url),
            )

            logger.info(
                "🔴 Starting red team scan job",
                extra={
                    "job_id": job_id,
                    "agent_url": str(job.request.evaluated_agent_url),
                    "scan_type": job.request.red_team_config.scan_type,
                    "vulnerabilities_count": len(
                        job.request.red_team_config.vulnerabilities,
                    ),
                    "attacks_count": len(job.request.red_team_config.attacks),
                },
            )

            # Update job status
            job.status = EvaluationStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            self._notify_job_update(job)

            # Wait for WebSocket client to connect before sending updates
            # This ensures chat messages aren't lost
            max_wait = 5.0  # seconds
            wait_interval = 0.1
            waited = 0.0
            while waited < max_wait:
                if self.websocket_manager.has_connections(job_id):
                    logger.info(
                        f"WebSocket client connected for job {job_id}, starting scan",
                    )
                    break
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            else:
                logger.warning(
                    f"No WebSocket client connected after {max_wait}s, "
                    f"proceeding anyway for job {job_id}",
                )

            # Create and run orchestrator
            orchestrator = RedTeamOrchestrator(
                protocol=job.request.evaluated_agent_protocol,
                transport=job.request.evaluated_agent_transport,
                evaluated_agent_url=(
                    str(job.request.evaluated_agent_url)
                    if job.request.evaluated_agent_url
                    else ""
                ),  # noqa: E501
                evaluated_agent_auth_type=job.request.evaluated_agent_auth_type,
                evaluated_agent_auth_credentials=job.request.evaluated_agent_auth_credentials,  # noqa: E501
                red_team_config=job.request.red_team_config,
                qualifire_api_key=job.request.qualifire_api_key,
                deckard_base_url=job.request.deckard_base_url,
                judge_llm=job.request.judge_llm,
                judge_llm_api_key=job.request.judge_llm_api_key,
                judge_llm_aws_access_key_id=job.request.judge_llm_aws_access_key_id,
                judge_llm_aws_secret_access_key=job.request.judge_llm_aws_secret_access_key,  # noqa: E501
                judge_llm_aws_region=job.request.judge_llm_aws_region,
                judge_llm_api_base=job.request.judge_llm_api_base,
                judge_llm_api_version=job.request.judge_llm_api_version,
                attacker_llm=job.request.attacker_llm,
                attacker_llm_api_key=job.request.attacker_llm_api_key,
                attacker_llm_aws_access_key_id=job.request.attacker_llm_aws_access_key_id,  # noqa: E501
                attacker_llm_aws_secret_access_key=job.request.attacker_llm_aws_secret_access_key,  # noqa: E501
                attacker_llm_aws_region=job.request.attacker_llm_aws_region,
                attacker_llm_api_base=job.request.attacker_llm_api_base,
                attacker_llm_api_version=job.request.attacker_llm_api_version,
                business_context=job.request.business_context,
                python_entrypoint_file=job.request.python_entrypoint_file,
            )

            # Stream updates from orchestrator
            async for update_type, data in orchestrator.run_scan():
                if update_type == "status":
                    # Status updates are logged but not sent via websocket
                    # Job status updates are handled by _notify_job_update
                    logger.info(f"Red team status: {data}")
                    job.progress = min(0.9, job.progress + 0.1)
                    self._notify_job_update(job)
                elif update_type == "chat":
                    logger.info(
                        f"📨 Red team chat update received for job {job_id}",
                        extra={"data": data},
                    )
                    self._send_websocket(
                        job_id,
                        WebSocketEventType.CHAT_UPDATE,
                        data,
                    )
                    job.progress = min(0.9, job.progress + 0.1)
                    self._notify_job_update(job)
                elif update_type == "results":
                    job.results = data
                    job.progress = 1.0
                    # Results are stored in job and sent via job update
                    self._notify_job_update(job)

            # Mark job as completed
            job.status = EvaluationStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            self._notify_job_update(job)

            logger.info(
                "✅ Red team scan completed successfully",
                extra={
                    "job_id": job_id,
                    "vulnerabilities_found": (
                        job.results.total_vulnerabilities_found if job.results else 0
                    ),
                },
            )

        except Exception as e:
            logger.exception(
                "❌ Red team scan failed",
                extra={"job_id": job_id, "error": str(e)},
            )
            job.status = EvaluationStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            self._notify_job_update(job)
            # Send error via websocket
            self._send_websocket(
                job_id,
                WebSocketEventType.ERROR,
                {"message": f"Red team scan failed: {str(e)}"},
            )

    def _notify_job_update(self, job: RedTeamJob):
        """Notify websocket clients about job status update."""
        message = WebSocketMessage(
            type=WebSocketEventType.JOB_UPDATE,
            job_id=job.job_id,
            data={
                "status": job.status.value,
                "progress": job.progress,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": (
                    job.completed_at.isoformat() if job.completed_at else None
                ),
                "error_message": job.error_message,
            },
        )
        asyncio.create_task(
            self.websocket_manager.broadcast_to_job(job.job_id, message),
        )

    def _send_websocket(
        self,
        job_id: str,
        event_type: WebSocketEventType,
        data: Any,
    ):
        """Send a websocket message to clients subscribed to this job."""
        try:
            message = WebSocketMessage(
                type=event_type,
                data=data,
                job_id=job_id,
            )
            asyncio.create_task(
                self.websocket_manager.broadcast_to_job(job_id, message),
            )
        except Exception as e:
            logger.error(
                f"Failed to send websocket message: {e}",
                extra={"job_id": job_id, "event_type": event_type.value},
            )
