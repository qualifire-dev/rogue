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
import uvicorn
from .main import app
from ..common.logging import configure_logger, get_logger

# Configure logging first
configure_logger()
logger = get_logger(__name__)


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

    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
        )
    except KeyboardInterrupt:
        logger.info(
            "Server stopped by user",
            extra={"component": "server_main", "event": "keyboard_interrupt"},
        )
        sys.exit(0)
    except Exception as e:
        logger.error(
            "Server failed to start",
            extra={
                "component": "server_main",
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
