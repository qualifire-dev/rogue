from functools import lru_cache
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from rogue_sdk.types import EvaluationJob, WebSocketEventType, WebSocketMessage

from ...common.logging.config import get_logger

logger = get_logger(__name__)

websocket_router = APIRouter(prefix="/ws", tags=["ws"])


class _WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]

    async def send_message(self, websocket: WebSocket, message: WebSocketMessage):
        try:
            await websocket.send_text(message.model_dump_json())
        except Exception:
            logger.exception("Error sending WebSocket message")

    async def broadcast_to_job(self, job_id: str, message: WebSocketMessage):
        if job_id not in self.active_connections:
            return

        disconnected = []
        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_text(message.model_dump_json())
            except Exception:
                logger.exception(f"Error broadcasting to job {job_id}")
                disconnected.append(websocket)

        # Clean up disconnected websockets
        for ws in disconnected:
            self.disconnect(ws, job_id)

    async def broadcast_job_update(self, job: EvaluationJob):
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

        # Send to job-specific connections
        await self.broadcast_to_job(job.job_id, message)


_websocket_manager: _WebSocketManager = None  # type: ignore


@lru_cache(1)
def get_websocket_manager() -> _WebSocketManager:
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = _WebSocketManager()
    return _websocket_manager


@websocket_router.websocket("/{job_id}")
async def websocket_job_endpoint(websocket: WebSocket, job_id: str):
    websocket_manager = get_websocket_manager()
    await websocket_manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, job_id)
