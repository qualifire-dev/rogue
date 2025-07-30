from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone
import sys
import platform

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    python_version: str
    platform: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
        python_version=sys.version,
        platform=platform.platform(),
    )
