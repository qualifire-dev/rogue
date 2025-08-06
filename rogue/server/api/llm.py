"""
LLM API endpoints - Server-native LLM operations.

This module provides REST API endpoints for LLM operations that were
previously handled by the legacy LLMService.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...services.llm_service import LLMService
from sdks.python.rogue_client.types import EvaluationResults, Scenarios
from ...common.logging import get_logger

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])
logger = get_logger(__name__)


class ScenarioGenerationRequest(BaseModel):
    """Request to generate test scenarios."""

    business_context: str
    model: str = "openai/gpt-4.1"
    api_key: Optional[str] = None
    count: int = 10


class ScenarioGenerationResponse(BaseModel):
    """Response containing generated scenarios."""

    scenarios: Scenarios
    message: str


class SummaryGenerationRequest(BaseModel):
    """Request to generate evaluation summary."""

    results: EvaluationResults
    model: str = "openai/gpt-4.1"
    api_key: Optional[str] = None


class SummaryGenerationResponse(BaseModel):
    """Response containing generated summary."""

    summary: str
    message: str


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
        logger.error(f"Failed to generate scenarios: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate scenarios: {str(e)}"
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
            summary=summary, message="Successfully generated evaluation summary"
        )

    except Exception as e:
        logger.error(f"Failed to generate summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate summary: {str(e)}"
        )
