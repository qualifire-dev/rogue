"""
Rogue Agent Evaluator Server

FastAPI-based server for the Rogue Agent Evaluator system.
Provides REST API endpoints and WebSocket support for agent evaluation.
"""

import warnings

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="websockets.legacy is deprecated",
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="websockets.server.WebSocketServerProtocol is deprecated",
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="remove second argument of ws_handler",
)

from . import api, core, models, services, websocket
