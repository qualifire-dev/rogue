from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import logging

from ..models.api_models import EvaluationJob, WebSocketMessage

logger = logging.getLogger(__name__)

websocket_router = APIRouter()


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: Optional[str] = None):
        await websocket.accept()

        if job_id:
            if job_id not in self.active_connections:
                self.active_connections[job_id] = []
            self.active_connections[job_id].append(websocket)
        else:
            # Global connection for all updates
            if "global" not in self.active_connections:
                self.active_connections["global"] = []
            self.active_connections["global"].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: Optional[str] = None):
        if job_id and job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]
        else:
            # Remove from global connections
            if "global" in self.active_connections:
                if websocket in self.active_connections["global"]:
                    self.active_connections["global"].remove(websocket)

    async def send_message(self, websocket: WebSocket, message: WebSocketMessage):
        try:
            await websocket.send_text(message.model_dump_json())
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")

    async def broadcast_to_job(self, job_id: str, message: WebSocketMessage):
        if job_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[job_id]:
                try:
                    await websocket.send_text(message.model_dump_json())
                except Exception as e:
                    logger.error(f"Error broadcasting to job {job_id}: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws, job_id)

    async def broadcast_global(self, message: WebSocketMessage):
        if "global" in self.active_connections:
            disconnected = []
            for websocket in self.active_connections["global"]:
                try:
                    await websocket.send_text(message.model_dump_json())
                except Exception as e:
                    logger.error(f"Error broadcasting globally: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws)

    async def broadcast_job_update(self, job: EvaluationJob):
        message = WebSocketMessage(
            type="job_update",
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

        # Send to global connections
        await self.broadcast_global(message)


# Global instance
websocket_manager = WebSocketManager()


@websocket_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)


@websocket_router.websocket("/ws/{job_id}")
async def websocket_job_endpoint(websocket: WebSocket, job_id: str):
    await websocket_manager.connect(websocket, job_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, job_id)
