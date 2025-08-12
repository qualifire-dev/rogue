"""
Rogue Agent Evaluator Server

Run the FastAPI server for the Rogue Agent Evaluator.

Usage:
    python -m rogue.server

Environment Variables:
    HOST: Server host (default: 127.0.0.1)
    PORT: Server port (default: 8000)
    RELOAD: Enable auto-reload for development (default: False)
"""

import os
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..common.logging import configure_logger, get_logger
from .api.evaluation import router as evaluation_router
from .api.health import router as health_router
from .api.interview import router as interview_router
from .api.llm import router as llm_router
from .websocket.manager import websocket_router

# Configure logging first
configure_logger()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting Rogue Agent Evaluator Server",
        extra={"component": "server", "event": "startup"},
    )
    yield
    logger.info(
        "Shutting down Rogue Agent Evaluator Server",
        extra={"component": "server", "event": "shutdown"},
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="Rogue Agent Evaluator API",
        description="API server for the Rogue Agent Evaluator system",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(evaluation_router, prefix="/api/v1")
    app.include_router(llm_router)
    app.include_router(interview_router)
    app.include_router(websocket_router)

    return app


def main():
    """Main entry point for the server."""
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() in ("true", "1", "yes")

    logger.info(
        "Starting Rogue Agent Evaluator Server",
        extra={
            "component": "server_main",
            "host": host,
            "port": port,
            "reload": reload,
            "api_docs_url": f"http://{host}:{port}/docs",
            "health_check_url": f"http://{host}:{port}/api/v1/health",
        },
    )

    app = create_app()

    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
        )
    except KeyboardInterrupt:
        logger.info("^C Server stopped by user")
        sys.exit(0)
    except Exception:
        logger.exception("Server failed to start")
        sys.exit(1)


if __name__ == "__main__":
    main()
