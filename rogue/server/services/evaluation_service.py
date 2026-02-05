import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from rogue_sdk.types import (
    EvaluationJob,
    EvaluationMode,
    EvaluationStatus,
    Scenarios,
    WebSocketEventType,
    WebSocketMessage,
)

from ...common.logging import get_logger, set_job_context
from ..core.evaluation_orchestrator import EvaluationOrchestrator
from ..websocket.manager import get_websocket_manager

logger = get_logger(__name__)


class EvaluationService:
    def __init__(self) -> None:
        self.jobs: Dict[str, EvaluationJob] = {}
        self.logger = get_logger(__name__)
        self.websocket_manager = get_websocket_manager()
        self._lock = asyncio.Lock()

    async def add_job(self, job: EvaluationJob):
        async with self._lock:
            self.jobs[job.job_id] = job

    async def get_job(self, job_id: str) -> Optional[EvaluationJob]:
        async with self._lock:
            return self.jobs.get(job_id)

    async def get_jobs(
        self,
        status: Optional[EvaluationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EvaluationJob]:
        async with self._lock:
            jobs = list(self.jobs.values())

        if status:
            jobs = [job for job in jobs if job.status == status]

        jobs.sort(key=lambda x: x.created_at, reverse=True)
        return jobs[offset : offset + limit]

    async def get_job_count(self, status: Optional[EvaluationStatus] = None) -> int:
        async with self._lock:
            if status:
                return len([job for job in self.jobs.values() if job.status == status])
            return len(self.jobs)

    async def cancel_job(self, job_id: str) -> bool:
        job = await self.get_job(job_id)
        if not job:
            return False

        if job.status in [EvaluationStatus.PENDING, EvaluationStatus.RUNNING]:
            job.status = EvaluationStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            self._notify_job_update(job)

        return True

    async def run_job(self, job_id: str):
        job = await self.get_job(job_id)
        if not job:
            return

        try:
            # Set job context for logging
            set_job_context(
                job_id=job_id,
                agent_url=str(job.request.agent_config.evaluated_agent_url),
            )

            logger.info(
                "Starting evaluation job",
                extra={
                    "job_status": "running",
                    "scenario_count": (
                        len(job.request.scenarios) if job.request.scenarios else 0
                    ),
                    "agent_url": str(job.request.agent_config.evaluated_agent_url),
                    "judge_llm": job.request.agent_config.judge_llm,
                },
            )

            job.status = EvaluationStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            self._notify_job_update(job)

            agent_config = job.request.agent_config

            # Route to appropriate orchestrator based on evaluation mode
            if agent_config.evaluation_mode == EvaluationMode.RED_TEAM:
                # Red team evaluation - should use /api/v1/red-team endpoint instead
                logger.error(
                    "Red team evaluation requests should be routed to "
                    "/api/v1/red-team endpoint, not the standard evaluation endpoint",
                )
                raise ValueError(
                    "Red team evaluation not supported on this endpoint. "
                    "Please use /api/v1/red-team endpoint",
                )

            # Create policy evaluation orchestrator
            scenarios = Scenarios(
                scenarios=job.request.scenarios if job.request.scenarios else [],
            )

            orchestrator = EvaluationOrchestrator(
                protocol=agent_config.protocol,
                transport=agent_config.transport,
                evaluated_agent_url=(
                    str(agent_config.evaluated_agent_url)
                    if agent_config.evaluated_agent_url
                    else ""
                ),
                evaluated_agent_auth_type=agent_config.evaluated_agent_auth_type,
                evaluated_agent_auth_credentials=(
                    agent_config.evaluated_agent_credentials
                ),
                judge_llm=agent_config.judge_llm,
                judge_llm_api_key=agent_config.judge_llm_api_key,
                judge_llm_aws_access_key_id=agent_config.judge_llm_aws_access_key_id,
                judge_llm_aws_secret_access_key=agent_config.judge_llm_aws_secret_access_key,  # noqa: E501
                judge_llm_aws_region=agent_config.judge_llm_aws_region,
                judge_llm_api_base=agent_config.judge_llm_api_base,
                judge_llm_api_version=agent_config.judge_llm_api_version,
                scenarios=scenarios,
                business_context=agent_config.business_context,
                deep_test_mode=agent_config.deep_test_mode,
                python_entrypoint_file=agent_config.python_entrypoint_file,
            )

            logger.info(
                "Starting server-native evaluation orchestrator",
                extra={
                    "agent_url": str(job.request.agent_config.evaluated_agent_url),
                    "judge_llm": job.request.agent_config.judge_llm,
                    "scenario_count": len(scenarios.scenarios),
                    "protocol": (
                        agent_config.protocol.value if agent_config.protocol else None
                    ),
                    "python_entrypoint_file": agent_config.python_entrypoint_file,
                },
            )

            # Process evaluation updates in real-time
            final_results = None
            async for update_type, data in orchestrator.run_evaluation():
                logger.debug(
                    "Evaluation progress update",
                    extra={
                        "update_type": update_type,
                        "data_preview": str(data)[:100] if data else None,
                    },
                )

                if update_type == "status":
                    # Update progress based on status messages
                    if "Running scenarios" in str(data):
                        job.progress = 0.1
                        self._notify_job_update(job)
                elif update_type == "chat":
                    # Real-time chat updates via WebSocket
                    logger.info(f"Received chat update for job {job_id}: {data}")
                    self._notify_chat_update(job_id, data)
                    job.progress = min(0.9, job.progress + 0.1)
                    self._notify_job_update(job)
                elif update_type == "results":
                    # Store final results
                    final_results = data

            logger.info("Server-native evaluation completed")

            # Update job with results
            # For red teaming, success means tests ran (even if no vulns found)
            has_results = final_results and (
                final_results.results
                or final_results.red_teaming_results
                or final_results.vulnerability_scan_log
                or final_results.owasp_summary
            )
            if has_results:
                # Type narrowing for mypy - has_results already checked final_results
                if final_results is None:
                    raise ValueError("Final results are None")
                # Store both the list (backward compat) and full results object
                job.results = final_results.results
                job.evaluation_results = final_results
                job.status = EvaluationStatus.COMPLETED
                job.progress = 1.0
                logger.info(
                    "Stored evaluation results",
                    extra={
                        "regular_results": (
                            len(final_results.results) if final_results.results else 0
                        ),
                        "red_team_results": (
                            len(final_results.red_teaming_results)
                            if final_results.red_teaming_results
                            else 0
                        ),
                        "vulnerability_scan_log": (
                            len(final_results.vulnerability_scan_log)
                            if final_results.vulnerability_scan_log
                            else 0
                        ),
                        "owasp_summary": (
                            len(final_results.owasp_summary)
                            if final_results.owasp_summary
                            else 0
                        ),
                    },
                )
            else:
                # No results - mark as failed
                job.status = EvaluationStatus.FAILED
                job.error_message = "Evaluation completed but no results were generated"

            logger.info(
                "Evaluation job completed successfully",
                extra={
                    "job_status": job.status.value,
                    "results_count": len(job.results) if job.results else 0,
                    "duration_seconds": (
                        (datetime.now(timezone.utc) - job.started_at).total_seconds()
                        if job.started_at
                        else None
                    ),
                },
            )

        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)

            # Provide user-friendly error messages
            if "APIError" in error_type and "Connection error" in error_msg:
                user_error = (
                    "LLM API Connection Error: Cannot connect to "
                    f"{job.request.agent_config.judge_llm}. "
                    "Please check your API key and network connection."
                )
            elif "APIError" in error_type and "authentication" in error_msg.lower():
                user_error = (
                    "LLM Authentication Error: Invalid API key for "
                    f"{job.request.agent_config.judge_llm}. "
                    "Please verify your judge_llm_api_key."
                )
            elif "timeout" in error_msg.lower():
                user_error = (
                    "Timeout Error: The evaluation took too long. "
                    "The agent under test may not be responding."
                )
            else:
                user_error = f"Evaluation error: {error_msg}"

            job.status = EvaluationStatus.FAILED
            job.error_message = user_error

            logger.exception(
                "Evaluation job failed",
                extra={
                    "job_status": "failed",
                    "duration_seconds": (
                        (datetime.now(timezone.utc) - job.started_at).total_seconds()
                        if job.started_at
                        else None
                    ),
                },
            )
        finally:
            job.completed_at = datetime.now(timezone.utc)
            self._notify_job_update(job)

    def _notify_job_update(self, job: EvaluationJob):
        asyncio.create_task(self.websocket_manager.broadcast_job_update(job))

    def _notify_chat_update(self, job_id: str, chat_data: Any):
        """Send real-time chat updates via WebSocket"""
        # Ensure chat_data is in the expected format
        if isinstance(chat_data, dict):
            # Chat data is already a dict with role/content
            data = chat_data
        else:
            # Convert string to dict format
            data = {"role": "assistant", "content": str(chat_data)}

        message = WebSocketMessage(
            type=WebSocketEventType.CHAT_UPDATE,
            job_id=job_id,
            data=data,
        )

        logger.debug(f"Sending chat update via WebSocket: {data}")
        asyncio.create_task(self.websocket_manager.broadcast_to_job(job_id, message))
