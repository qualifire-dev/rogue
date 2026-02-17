import click
import uvicorn
from loguru import logger

from .chat_completions_wrapper import app


@click.command()
@click.option("--host", "host", default="127.0.0.1", help="Host to run the server on")
@click.option("--port", "port", default=10001, help="Port to run the server on")
def main(host: str, port: int) -> None:
    logger.info(f"Starting test agent on http://{host}:{port}")
    logger.info(f"Endpoint: http://{host}:{port}/chat/completions")
    uvicorn.run(
        app,
        host=host,
        port=port,
    )


if __name__ == "__main__":
    main()
