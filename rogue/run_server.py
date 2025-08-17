import os
from argparse import ArgumentParser, Namespace

from .server.main import start_server


def set_server_args(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "127.0.0.1"),
        help="Host to run the server on. defaults to the HOST env or 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Port to run the server on. defaults to the PORT env or 8000",
    )


def run_server(args: Namespace) -> None:
    start_server(
        host=args.host,
        port=args.port,
    )
