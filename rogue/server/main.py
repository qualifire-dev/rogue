from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .api.evaluation import router as evaluation_router
from .api.health import router as health_router
from .websocket.manager import websocket_router
from ..common.logging import get_logger

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
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(evaluation_router, prefix="/api/v1")
    app.include_router(websocket_router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    import os

    host = os.getenv("HOST", "127.0.0.1")  # Default to localhost for security
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
