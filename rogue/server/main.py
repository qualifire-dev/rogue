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
import socket
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..common.logging import configure_logger, get_logger
from .api.config import router as config_router
from .api.evaluation import router as evaluation_router
from .api.health import router as health_router
from .api.interview import router as interview_router
from .api.llm import router as llm_router
from .api.red_team import router as red_team_router
from .websocket.manager import websocket_router

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

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        errors = [{k: v for k, v in e.items() if k != "ctx"} for e in exc.errors()]
        logger.error(
            "Validation error",
            extra={"errors": errors},
        )
        return JSONResponse(status_code=422, content={"detail": errors})

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(evaluation_router, prefix="/api/v1")
    app.include_router(red_team_router, prefix="/api/v1")
    app.include_router(llm_router, prefix="/api/v1")
    app.include_router(interview_router, prefix="/api/v1")
    app.include_router(config_router, prefix="/api/v1")
    app.include_router(websocket_router, prefix="/api/v1")

    _mount_web_ui(app)

    return app


def _resolve_web_dist() -> Path | None:
    """Locate the bundled SPA — installed wheel layout, or source-tree fallback."""
    bundled = Path(__file__).resolve().parent.parent / "web_dist"
    if (bundled / "index.html").is_file():
        return bundled
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "packages" / "web" / "dist"
        if (candidate / "index.html").is_file():
            return candidate
    return None


def _mount_web_ui(app: FastAPI) -> None:
    """Serve the bundled SPA when present.

    The SPA is bundled into ``rogue/web_dist/`` by the wheel build (Hatch
    force-include of ``packages/web/dist``). When absent (e.g. dev install
    without ``pnpm build``), this is a no-op and the API still works.

    Hashed assets are mounted at ``/assets``; every other non-API GET returns
    ``index.html`` so client-side routes deep-link cleanly.
    """
    web_dist = _resolve_web_dist()
    if web_dist is None:
        return
    index_html = web_dist / "index.html"

    assets_dir = web_dist / "assets"
    if assets_dir.is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="web-assets",
        )

    # Top-level static files (favicon, rogue_logo.svg, robots.txt, ...)
    @app.get("/{filename:path}", include_in_schema=False)
    async def spa_fallback(filename: str):
        # Never shadow API routes or WebSocket endpoints.
        if (
            filename.startswith("api/")
            or filename.startswith("ws/")
            or filename == "docs"
            or filename == "redoc"
            or filename == "openapi.json"
        ):
            raise HTTPException(status_code=404)
        # Serve a known static file if it exists, otherwise hand back the SPA.
        candidate = web_dist / filename
        if filename and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(index_html))


def start_server(
    host: str,
    port: int,
    reload: bool = False,
    log_file: Path | None = None,
):
    configure_logger(file_path=log_file)
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

    # Check if port is already in use before starting
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        result = sock.connect_ex((host, port))
        if result == 0:
            logger.error(
                f"Port {port} is already in use. "
                f"Please stop the other process or use a different port "
                f"(set PORT environment variable).",
                extra={"component": "server_main", "host": host, "port": port},
            )
            sys.exit(1)

    app = create_app()

    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_config=None,  # We are intercepting uvicorn logging to loguru
            log_level=None,  # We are intercepting uvicorn logging to loguru
        )
    except KeyboardInterrupt:
        logger.info("^C Server stopped by user")
        sys.exit(0)
    except Exception:
        logger.exception("Server failed to start")
        sys.exit(1)


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() in ("true", "1", "yes")
    start_server(host, port, reload)
