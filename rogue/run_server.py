import multiprocessing
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


def run_server_in_background(
    host: str,
    port: int,
    reload: bool = False,
) -> multiprocessing.Process:
    proccess = multiprocessing.Process(
        target=start_server,
        args=(host, port, reload),
    )
    proccess.start()
    return proccess


def run_server(args: Namespace, background: bool = False) -> None:
    # The host/port are missing when running `rogue-ai` without any args.
    # They are only included in the `args` object when running `rogue-ai server`
    try:
        host = args.host
    except AttributeError:
        host = os.getenv("HOST", "127.0.0.1")
    try:
        port = args.port
    except AttributeError:
        port = int(os.getenv("PORT", "8000"))

    if background:
        run_server_in_background(
            host=host,
            port=port,
            reload=False,
        )
    else:
        start_server(
            host=host,
            port=port,
            reload=False,
        )
