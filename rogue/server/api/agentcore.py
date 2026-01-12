from fastapi import APIRouter, BackgroundTasks, Depends
from rogue_sdk.types import EvaluationRequest, EvaluationResponse
from .evaluation import get_evaluation_service, enqueue_evaluation
from ..services.evaluation_service import EvaluationService

router = APIRouter(tags=["agentcore"])


@router.get("/ping")
def ping():
    return {"status": "Healthy"}


@router.post("/invocations", response_model=EvaluationResponse)
async def invocations(
        request: EvaluationRequest,
        background_tasks: BackgroundTasks,
        evaluation_service: EvaluationService = Depends(get_evaluation_service),
):
    #  different entrypoint to /evaluations to meet agentcore convention
    return await enqueue_evaluation(
        request=request,
        background_tasks=background_tasks,
        evaluation_service=evaluation_service,
        endpoint="/invocations",
    )
