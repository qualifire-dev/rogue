"""
Rogue Agent Evaluator Server

FastAPI-based server for the Rogue Agent Evaluator system.
Provides REST API endpoints and WebSocket support for agent evaluation.
"""

from . import api, core, services, websocket
