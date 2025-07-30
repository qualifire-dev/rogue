import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from ..models.api_models import EvaluationJob, EvaluationStatus
from ..websocket.manager import websocket_manager
from ...services.evaluation_library import EvaluationLibrary
from ...models.scenario import Scenarios
from ...common.logging import get_logger, set_job_context


class EvaluationService:
    def __init__(self):
        self.jobs: Dict[str, EvaluationJob] = {}
        self.logger = get_logger(__name__)

    def add_job(self, job: EvaluationJob):
        self.jobs[job.job_id] = job

    def get_job(self, job_id: str) -> Optional[EvaluationJob]:
        return self.jobs.get(job_id)

    def get_jobs(
        self,
        status: Optional[EvaluationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EvaluationJob]:
        jobs = list(self.jobs.values())
        if status:
            jobs = [job for job in jobs if job.status == status]

        jobs.sort(key=lambda x: x.created_at, reverse=True)
        return jobs[offset : offset + limit]

    def get_job_count(self, status: Optional[EvaluationStatus] = None) -> int:
        if status:
            return len([job for job in self.jobs.values() if job.status == status])
        return len(self.jobs)

    def cancel_job(self, job_id: str) -> bool:
        job = self.jobs.get(job_id)
        if not job:
            return False

        if job.status in [EvaluationStatus.PENDING, EvaluationStatus.RUNNING]:
            job.status = EvaluationStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            self._notify_job_update(job)

        return True

    async def run_evaluation(self, job_id: str):
        job = self.jobs.get(job_id)
        if not job:
            return

        try:
            # Set job context for logging
            set_job_context(
                job_id=job_id, agent_url=str(job.request.agent_config.agent_url)
            )

            self.logger.info(
                "Starting evaluation job",
                extra={
                    "job_status": "running",
                    "scenario_count": len(job.request.scenarios),
                    "agent_url": str(job.request.agent_config.agent_url),
                    "judge_llm": job.request.agent_config.judge_llm,
                },
            )

            job.status = EvaluationStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            self._notify_job_update(job)

            # Convert request scenarios to Scenarios object
            scenarios = Scenarios(scenarios=job.request.scenarios)

            # Create progress callback for real-time updates
            def progress_callback(update_type: str, data: Any):
                self.logger.debug(
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
                    elif "conversation" in str(data).lower():
                        # Estimate progress based on conversations
                        job.progress = min(0.9, job.progress + 0.1)
                    self._notify_job_update(job)
                elif update_type == "chat":
                    # Real-time chat updates via WebSocket
                    self._notify_chat_update(job_id, data)

            # Use the library interface directly
            self.logger.info(
                "Calling evaluation library",
                extra={"business_context": "The agent provides customer service."},
            )

            evaluation_results = await EvaluationLibrary.evaluate_agent(
                agent_config=job.request.agent_config,
                scenarios=scenarios,
                business_context="The agent provides customer service.",
                progress_callback=progress_callback,
            )

            # Update job with results
            job.results = evaluation_results.results
            job.status = EvaluationStatus.COMPLETED
            job.progress = 1.0

            self.logger.info(
                "Evaluation job completed successfully",
                extra={
                    "job_status": "completed",
                    "results_count": len(evaluation_results.results),
                    "duration_seconds": (
                        (datetime.now(timezone.utc) - job.started_at).total_seconds()
                        if job.started_at
                        else None
                    ),
                },
            )

        except Exception as e:
            job.status = EvaluationStatus.FAILED
            job.error_message = f"Evaluation error: {str(e)}"

            self.logger.error(
                "Evaluation job failed",
                extra={
                    "job_status": "failed",
                    "error": str(e),
                    "error_type": type(e).__name__,
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
        asyncio.create_task(websocket_manager.broadcast_job_update(job))

    def _notify_chat_update(self, job_id: str, chat_data: Any):
        """Send real-time chat updates via WebSocket"""
        from ..models.api_models import WebSocketMessage

        message = WebSocketMessage(
            type="chat_update", job_id=job_id, data={"message": str(chat_data)}
        )

        asyncio.create_task(websocket_manager.broadcast_to_job(job_id, message))
