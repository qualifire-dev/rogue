"""
LLM API endpoints - Server-native LLM operations.

This module provides REST API endpoints for LLM operations.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from rogue_sdk.types import (
    ScenarioGenerationRequest,
    ScenarioGenerationResponse,
    SummaryGenerationRequest,
    ReportSummaryResponse,
    ReportSummaryRequest,
)

from rogue.server.api.evaluation import get_evaluation_service
from rogue.server.services.evaluation_service import EvaluationService

from ..models.api_format import ServerSummaryGenerationResponse

from ...common.logging import get_logger
from ..services.llm_service import LLMService
from ..services.qualifire_service import QualifireService

router = APIRouter(prefix="/llm", tags=["llm"])
logger = get_logger(__name__)


@router.post("/scenarios", response_model=ScenarioGenerationResponse)
async def generate_scenarios(request: ScenarioGenerationRequest):
    """
    Generate test scenarios based on business context.

    This endpoint replaces direct calls to LLMService.generate_scenarios().
    """
    try:
        logger.info(
            "Generating scenarios via API",
            extra={
                "business_context_length": len(request.business_context),
                "model": request.model,
                "count": request.count,
            },
        )

        scenarios = LLMService.generate_scenarios(
            model=request.model,
            context=request.business_context,
            llm_provider_api_key=request.api_key,
        )

        logger.info(f"Successfully generated {len(scenarios.scenarios)} scenarios")

        return ScenarioGenerationResponse(
            scenarios=scenarios,
            message=f"Successfully generated {len(scenarios.scenarios)} scenarios",
        )

    except Exception as e:
        logger.exception("Failed to generate scenarios")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate scenarios: {str(e)}",
        )


@router.post(
    "/summary",
    response_model=ServerSummaryGenerationResponse,
)
async def generate_summary(
    request: SummaryGenerationRequest,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
) -> ServerSummaryGenerationResponse:
    """
    Generate evaluation summary from results.

    This endpoint replaces direct calls to LLMService.generate_summary_from_results().
    """
    try:
        logger.info(
            "Generating summary via API",
            extra={
                "model": request.model,
                "results_count": len(request.results.results),
            },
        )

        summary = LLMService.generate_summary_from_results(
            model=request.model,
            results=request.results,
            llm_provider_api_key=request.api_key,
        )

        logger.info("Successfully generated evaluation summary")

        logger.info(
            "Qualifire API key",
            extra={"qualifire_api_key": request.qualifire_api_key},
        )
        logger.info(
            "Job ID",
            extra={"job_id": request.job_id},
        )
        logger.info(
            "Qualifire URL",
            extra={"qualifire_url": request.qualifire_url},
        )

        if request.qualifire_api_key and request.job_id:

            logger.info(
                "Reporting summary to Qualifire",
                extra={"job_id": request.job_id},
            )

            job = await evaluation_service.get_job(request.job_id)

            if not job and not request.judge_model and not request.deep_test:
                raise HTTPException(
                    status_code=400,
                    detail="Job not found and judge model and deep test are not provided",  # noqa: E501
                )

            logger.info(
                "Summary",
                extra={"summary": summary, "results": request.results},
            )

            QualifireService.report_summary(
                ReportSummaryRequest(
                    job_id=request.job_id,
                    structured_summary=summary,
                    deep_test=job.deep_test if job else request.deep_test,
                    start_time=(
                        job.created_at
                        if job is not None
                        else datetime.now(timezone.utc)
                    ),
                    judge_model=job.judge_model if job else request.judge_model,
                    qualifire_url=request.qualifire_url,
                    qualifire_api_key=request.qualifire_api_key,
                ),
                evaluation_result=request.results,
            )

        return ServerSummaryGenerationResponse(
            summary=summary,
            message="Successfully generated evaluation summary",
        )

    except Exception as e:
        logger.exception("Failed to generate summary")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}",
        )


@router.post("/report_summary", response_model=ReportSummaryResponse)
async def report_summary_handler(
    request: ReportSummaryRequest,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
):
    """
    Report summary to Qualifire.
    """
    try:
        job = await evaluation_service.get_job(request.job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Evaluation job not found",
            )

        results = job.results

        if not results or len(results) == 0:
            raise HTTPException(
                status_code=404,
                detail="Evaluation results not found or empty",
            )

        QualifireService.report_summary(
            request,
            evaluation_result=results[0],
        )

        return ReportSummaryResponse(
            success=True,
        )
    except Exception as e:
        logger.exception("Failed to report summary")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to report summary: {str(e)}",
        )
