"""
LLM API endpoints - Server-native LLM operations.

This module provides REST API endpoints for LLM operations.
"""

from fastapi import APIRouter, HTTPException
from rogue_sdk.types import (
    ScenarioGenerationRequest,
    ScenarioGenerationResponse,
    SummaryGenerationRequest,
    SummaryGenerationResponse,
)

from ...common.logging import get_logger
from ..services.llm_service import LLMService

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


@router.post("/summary", response_model=SummaryGenerationResponse)
async def generate_summary(request: SummaryGenerationRequest):
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

        return SummaryGenerationResponse(
            summary=summary,
            message="Successfully generated evaluation summary",
        )

    except Exception as e:
        logger.exception("Failed to generate summary")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}",
        )
