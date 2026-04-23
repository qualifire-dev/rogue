import multiprocessing
import os
import socket
import time
from argparse import ArgumentParser, Namespace

from pathlib import Path

import psutil
import requests
from loguru import logger

from .common.network import get_host_for_url
from .server.main import start_server


def is_pid_listening_on_port(pid: int, port: int, host: str = "127.0.0.1") -> bool:
    """
    Check if a specific PID is listening on a specific port.

    Args:
        pid: Process ID to check
        port: Port number to check
        host: Host address to check (default: 127.0.0.1)

    Returns:
        True if the PID is listening on the specified port, False otherwise
    """
    # First check if the process is alive
    try:
        process = psutil.Process(pid)
        if not process.is_running():
            return False

        # Get all network connections for this process
        connections = process.net_connections(kind="inet")

        for conn in connections:
            if (
                conn.status == psutil.CONN_LISTEN
                and conn.laddr.port == port
                and (
                    host == "0.0.0.0"  # nosec B104
                    or conn.laddr.ip == host
                    or conn.laddr.ip == "0.0.0.0"  # nosec B104
                )
            ):
                return True
        return False
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False


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
    timeout: float = 30.0,
) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not process.is_alive():
            return False

        # Check if the server subprocess is listening on the port
        pid = process.pid
        if pid is not None and is_pid_listening_on_port(int(pid), port, host):
            # Double-check with HTTP request to ensure the server is fully ready
            try:
                # Normalize host for HTTP requests (handle 0.0.0.0/:: and IPv6)
                http_host = get_host_for_url(host)

                response = requests.get(
                    f"http://{http_host}:{port}/api/v1/health",
                    timeout=1.0,
                )  # nosec B113
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                # Port is listening but server not ready yet, continue waiting
                pass

        time.sleep(0.3)

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

    # Check if port is already in use before starting
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sock.connect_ex((host, port)) == 0:
            raise Exception(
                f"Port {port} is already in use. "
                f"Please stop the other process or use a different port "
                f"(set PORT environment variable).",
            )

    if background:
        process = run_server_in_background(
            host=host,
            port=port,
            reload=False,
            log_file=log_file,
        )
        if background_wait_for_ready:
            if not wait_until_server_ready(process, host, port):
                # Terminate the orphan process before raising
                process.terminate()
                process.join(timeout=5)
                raise Exception("Server failed to start")
            logger.info("Rogue server ready", extra={"host": host, "port": port})
        return process
    else:
        return start_server(
            host=host,
            port=port,
            reload=False,
            log_file=log_file,
        )
