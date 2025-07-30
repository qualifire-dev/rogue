"""
WebSocket Client for Rogue Agent Evaluator real-time updates.
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict, List, Any
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from websockets.client import ClientConnection

from .types import WebSocketMessage, WebSocketEventType

logger = logging.getLogger(__name__)


class RogueWebSocketClient:
    """WebSocket client for real-time updates."""

    def __init__(self, base_url: str, job_id: Optional[str] = None):
        self.base_url = base_url.replace("http", "ws").rstrip("/")
        self.job_id = job_id
        self.websocket: Optional["ClientConnection"] = None
        self.event_handlers: Dict[WebSocketEventType, List[Callable]] = {}
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1.0
        self._stop_event = asyncio.Event()

    async def connect(self) -> None:
        """Connect to WebSocket."""
        if self.is_connected:
            return

        ws_url = f"{self.base_url}/ws"
        if self.job_id:
            ws_url = f"{self.base_url}/ws/{self.job_id}"

        try:
            self.websocket = await websockets.connect(
                ws_url,
            )  # type: ignore[assignment]
            self.is_connected = True
            self.reconnect_attempts = 0
            self._emit("connected", {"url": ws_url})

            # Start message handling task
            asyncio.create_task(self._handle_messages())

        except Exception as e:
            self._emit("error", {"error": str(e)})
            raise

    async def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        self._stop_event.set()
        self.is_connected = False

        if self.websocket:
            await self.websocket.close()  # type: ignore[attr-defined]
            self.websocket = None

        self._emit("disconnected", {})

    def on(self, event: WebSocketEventType, handler: Callable) -> None:
        """Add event handler."""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)

    def off(self, event: WebSocketEventType, handler: Callable) -> None:
        """Remove event handler."""
        if event in self.event_handlers:
            try:
                self.event_handlers[event].remove(handler)
            except ValueError:
                pass

    def remove_all_listeners(self, event: Optional[WebSocketEventType] = None) -> None:
        """Remove all event handlers."""
        if event:
            self.event_handlers.pop(event, None)
        else:
            self.event_handlers.clear()

    async def _handle_messages(self) -> None:
        """Handle incoming WebSocket messages."""
        try:
            while not self._stop_event.is_set() and self.websocket:
                try:
                    message_data = await asyncio.wait_for(
                        self.websocket.recv(), timeout=1.0  # type: ignore[attr-defined]
                    )

                    try:
                        message_dict = json.loads(message_data)
                        message = WebSocketMessage(**message_dict)
                        await self._handle_message(message)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"Failed to parse WebSocket message: {e}")

                except asyncio.TimeoutError:
                    # Timeout is expected, continue loop
                    continue
                except ConnectionClosed:
                    logger.info("WebSocket connection closed")
                    break
                except WebSocketException as e:
                    logger.error(f"WebSocket error: {e}")
                    break

        except Exception as e:
            logger.error(f"Error in message handler: {e}")
        finally:
            self.is_connected = False
            if self.reconnect_attempts < self.max_reconnect_attempts:
                await self._schedule_reconnect()

    async def _handle_message(self, message: WebSocketMessage) -> None:
        """Handle a parsed WebSocket message."""
        if message.type == "job_update":
            self._emit("job_update", message.data)
        elif message.type == "chat_update":
            self._emit("chat_update", message.data)
        else:
            logger.warning(f"Unknown WebSocket message type: {message.type}")

    def _emit(self, event: WebSocketEventType, data: Any) -> None:
        """Emit event to handlers."""
        handlers = self.event_handlers.get(event, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(event, data))
                else:
                    handler(event, data)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

    async def _schedule_reconnect(self) -> None:
        """Schedule reconnection attempt."""
        if self._stop_event.is_set():
            return

        self.reconnect_attempts += 1
        delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))

        logger.info(
            f"Scheduling reconnect attempt {self.reconnect_attempts} in {delay}s"
        )
        await asyncio.sleep(delay)

        if not self._stop_event.is_set():
            try:
                await self.connect()
            except Exception as e:
                logger.error(f"Reconnection failed: {e}")
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    await self._schedule_reconnect()
