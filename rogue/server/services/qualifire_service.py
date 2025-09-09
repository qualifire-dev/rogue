import requests
from loguru import logger

from .api_format_service import convert_with_structured_summary
from rogue_sdk.types import EvaluationResult, ReportSummaryRequest


class QualifireService:
    @staticmethod
    def report_summary(
        request: ReportSummaryRequest,
        evaluation_result: EvaluationResult,
    ):
        logger.info(
            "Reporting summary to Qualifire",
        )

        api_evaluation_result = convert_with_structured_summary(
            evaluation_results=evaluation_result,
            structured_summary=request.structured_summary,
            deep_test=request.deep_test,
            start_time=request.start_time,
            judge_model=request.judge_model,
        )

        response = requests.post(
            f"{request.qualifire_url}/api/rogue/v1/report",
            headers={"X-qualifire-key": request.qualifire_api_key},
            json=api_evaluation_result.model_dump(mode="json"),
            timeout=300,
        )

        if not response.ok:
            logger.error(
                "Failed to report summary to Qualifire",
                extra={"response": response.json()},
            )
            raise Exception(f"Failed to report summary to Qualifire: {response.json()}")

        return response.json()
