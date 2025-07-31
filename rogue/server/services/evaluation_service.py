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
                job_id=job_id,
                agent_url=str(job.request.agent_config.evaluated_agent_url),
            )

            self.logger.info(
                "Starting evaluation job",
                extra={
                    "job_status": "running",
                    "scenario_count": len(job.request.scenarios),
                    "agent_url": str(job.request.agent_config.evaluated_agent_url),
                    "judge_llm": job.request.agent_config.judge_llm_model,
                },
            )

            job.status = EvaluationStatus.RUNNING
            job.started_at = datetime.now(timezone.utc)
            self._notify_job_update(job)

            # Convert SDK scenarios to legacy scenarios for the evaluation service
            from ...models.scenario import (
                Scenario as LegacyScenario,
                ScenarioType as LegacyScenarioType,
            )

            self.logger.info(
                f"Converting {len(job.request.scenarios)} SDK scenarios to "
                "legacy format"
            )

            legacy_scenarios = []
            for i, sdk_scenario in enumerate(job.request.scenarios):
                # Convert SDK scenario to legacy scenario

                legacy_scenario_type = (
                    LegacyScenarioType.POLICY
                    if sdk_scenario.scenario_type.value == "policy"
                    else LegacyScenarioType.PROMPT_INJECTION
                )

                legacy_scenario = LegacyScenario(
                    scenario=sdk_scenario.scenario,
                    scenario_type=legacy_scenario_type,
                    dataset=sdk_scenario.dataset,
                    dataset_sample_size=sdk_scenario.dataset_sample_size,
                    expected_outcome=sdk_scenario.expected_outcome,
                )

                legacy_scenarios.append(legacy_scenario)

            scenarios = Scenarios(scenarios=legacy_scenarios)
            self.logger.info(
                (
                    "Successfully created Scenarios object with "
                    f"{len(scenarios.scenarios)} scenarios"
                )
            )

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
                    self.logger.info(f"Received chat update for job {job_id}: {data}")
                    self._notify_chat_update(job_id, data)

            # Use the library interface directly
            self.logger.info(
                "Calling evaluation library",
                extra={
                    "business_context": "The agent provides customer service.",
                    "agent_url": str(job.request.agent_config.evaluated_agent_url),
                    "judge_llm": job.request.agent_config.judge_llm_model,
                    "scenario_count": len(scenarios.scenarios),
                },
            )

            evaluation_results = await EvaluationLibrary.evaluate_agent(
                agent_config=job.request.agent_config,
                scenarios=scenarios,
                # TODO: FIX THIS!@!!!!!!
                business_context="",
                progress_callback=progress_callback,
            )

            self.logger.info("Evaluation library returned results")

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
            error_type = type(e).__name__
            error_msg = str(e)

            # Provide user-friendly error messages
            if "APIError" in error_type and "Connection error" in error_msg:
                user_error = (
                    "LLM API Connection Error: Cannot connect to "
                    f"{job.request.agent_config.judge_llm_model}. "
                    "Please check your API key and network connection."
                )
            elif "APIError" in error_type and "authentication" in error_msg.lower():
                user_error = (
                    "LLM Authentication Error: Invalid API key for "
                    f"{job.request.agent_config.judge_llm_model}. "
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

            self.logger.error(
                "Evaluation job failed",
                extra={
                    "job_status": "failed",
                    "error": error_msg,
                    "error_type": error_type,
                    "user_error": user_error,
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

        # Ensure chat_data is in the expected format
        if isinstance(chat_data, dict):
            # Chat data is already a dict with role/content
            data = chat_data
        else:
            # Convert string to dict format
            data = {"role": "assistant", "content": str(chat_data)}

        message = WebSocketMessage(
            type="chat_update",
            job_id=job_id,
            data=data,
        )

        self.logger.debug(f"Sending chat update via WebSocket: {data}")
        asyncio.create_task(websocket_manager.broadcast_to_job(job_id, message))
