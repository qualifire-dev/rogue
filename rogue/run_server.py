import multiprocessing
import os
import time
from argparse import ArgumentParser, Namespace
from pathlib import Path

import requests

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
    log_file: Path | None = None,
) -> multiprocessing.Process:
    proccess = multiprocessing.Process(
        target=start_server,
        args=(host, port, reload, log_file),
    )
    proccess.start()
    return proccess


def wait_until_server_ready(
    process: multiprocessing.Process,
    host: str,
    port: int,
    timeout: float = 10.0,
) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not process.is_alive():
            return False
        try:
            response = requests.get(f"http://{host}:{port}/api/v1/health")  # nosec B113
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(0.5)

    return False


def run_server(
    args: Namespace,
    background: bool = False,
    background_wait_for_ready: bool = True,
    log_file: Path | None = None,
) -> multiprocessing.Process | None:
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
        process = run_server_in_background(
            host=host,
            port=port,
            reload=False,
            log_file=log_file,
        )
        if background_wait_for_ready:
            if not wait_until_server_ready(process, host, port):
                raise Exception("Server failed to start")
        return process
    else:
        return start_server(
            host=host,
            port=port,
            reload=False,
            log_file=log_file,
        )
