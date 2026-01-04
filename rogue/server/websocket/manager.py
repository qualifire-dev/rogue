import asyncio
from functools import lru_cache
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from rogue_sdk.types import EvaluationJob, WebSocketEventType, WebSocketMessage
from starlette.websockets import WebSocketState

from ...common.logging.config import get_logger

logger = get_logger(__name__)

websocket_router = APIRouter(prefix="/ws", tags=["ws"])

# WebSocket keepalive configuration
# These values are tuned to prevent "keepalive ping timeout" errors during long-running
# operations like red team scans (which can last up to an hour or more)
PING_INTERVAL_SECONDS = 20  # Send ping every 20 seconds
PING_TIMEOUT_SECONDS = 120  # 2 min pong wait (generous for network hiccups)
RECEIVE_TIMEOUT_SECONDS = 300  # 5 min receive timeout (continues on timeout)


class _WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._ping_tasks: Dict[int, asyncio.Task] = {}  # Track ping tasks by ws id

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

        # Start keepalive ping task for this connection
        ws_id = id(websocket)
        self._ping_tasks[ws_id] = asyncio.create_task(
            self._keepalive_ping(websocket, job_id),
        )

        logger.debug(
            "WebSocket connected",
            extra={"job_id": job_id, "ws_id": ws_id},
        )

    async def _keepalive_ping(self, websocket: WebSocket, job_id: str):
        """Send periodic ping frames to keep the WebSocket connection alive.

        This prevents timeout errors during long-running operations like red team scans.
        The gorilla/websocket client (used by the TUI) expects ping/pong to keep
        connections alive.
        """
        ws_id = id(websocket)
        try:
            while True:
                await asyncio.sleep(PING_INTERVAL_SECONDS)

                # Check if websocket is still connected
                if websocket.client_state != WebSocketState.CONNECTED:
                    logger.debug(
                        "WebSocket no longer connected, stopping ping task",
                        extra={"job_id": job_id, "ws_id": ws_id},
                    )
                    break

                try:
                    # Send a ping frame to keep the connection alive
                    # FastAPI/Starlette WebSocket uses send() with bytes for ping
                    await websocket.send_bytes(b"ping")
                    logger.debug(
                        "Sent keepalive ping",
                        extra={"job_id": job_id, "ws_id": ws_id},
                    )
                except Exception as e:
                    logger.debug(
                        "Failed to send ping, connection may be closed",
                        extra={"job_id": job_id, "ws_id": ws_id, "error": str(e)},
                    )
                    break

        except asyncio.CancelledError:
            logger.debug(
                "Ping task cancelled",
                extra={"job_id": job_id, "ws_id": ws_id},
            )
        except Exception as e:
            logger.warning(
                "Ping task error",
                extra={"job_id": job_id, "ws_id": ws_id, "error": str(e)},
            )

    def disconnect(self, websocket: WebSocket, job_id: str):
        ws_id = id(websocket)

        # Cancel the ping task for this connection
        if ws_id in self._ping_tasks:
            self._ping_tasks[ws_id].cancel()
            del self._ping_tasks[ws_id]

        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]

        logger.debug(
            "WebSocket disconnected",
            extra={"job_id": job_id, "ws_id": ws_id},
        )

    def has_connections(self, job_id: str) -> bool:
        """Check if there are any active WebSocket connections for a job."""
        return (
            job_id in self.active_connections
            and len(self.active_connections[job_id]) > 0
        )

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
    """WebSocket endpoint for real-time job updates.

    This endpoint handles long-running connections during evaluation jobs.
    It includes keepalive mechanisms to prevent timeout errors during
    extended operations like red team scans.
    """
    websocket_manager = get_websocket_manager()
    await websocket_manager.connect(websocket, job_id)
    try:
        while True:
            # Use receive() instead of receive_text() to handle all message types
            # including ping/pong frames and binary messages
            try:
                message = await asyncio.wait_for(
                    websocket.receive(),
                    timeout=RECEIVE_TIMEOUT_SECONDS,
                )

                # Handle different message types
                msg_type = message.get("type", "")

                if msg_type == "websocket.disconnect":
                    logger.debug(
                        "Received disconnect message",
                        extra={"job_id": job_id},
                    )
                    break
                elif msg_type == "websocket.receive":
                    # Handle text or bytes data - this keeps the connection alive
                    # Client may send keepalive messages or actual commands
                    text_data = message.get("text")
                    bytes_data = message.get("bytes")
                    if text_data:
                        logger.debug(
                            "Received text message",
                            extra={"job_id": job_id, "data": text_data[:100]},
                        )
                    elif bytes_data:
                        # Binary data - could be ping response
                        logger.debug(
                            "Received binary message (possible pong)",
                            extra={"job_id": job_id},
                        )

            except asyncio.TimeoutError:
                # No message received within timeout, but that's okay
                # The ping task keeps the connection alive
                # Just continue waiting for messages
                logger.debug(
                    "WebSocket receive timeout, connection still alive",
                    extra={"job_id": job_id},
                )
                continue

    except WebSocketDisconnect as e:
        logger.debug(
            "WebSocket disconnected",
            extra={"job_id": job_id, "code": e.code if hasattr(e, "code") else None},
        )
    except Exception as e:
        logger.warning(
            "WebSocket error",
            extra={"job_id": job_id, "error": str(e)},
        )
    finally:
        websocket_manager.disconnect(websocket, job_id)
