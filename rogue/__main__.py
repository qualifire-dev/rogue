import asyncio
import subprocess  # nosec: B404
import sys
import time
from argparse import ArgumentParser, Namespace
from pathlib import Path

import platformdirs
from dotenv import load_dotenv
from loguru import logger

try:
    from . import __version__
except ImportError:
    # Fallback if running directly
    # Add parent directory to path
    import sys  # noqa: F811
    from pathlib import Path  # noqa: F811

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from rogue import __version__  # noqa: F401

from .common.logging.config import configure_logger
from .common.tui_installer import RogueTuiInstaller
from .common.update_checker import check_for_updates
from .run_cli import run_cli, set_cli_args
from .run_server import run_server, set_server_args
from .run_tui import run_rogue_tui

load_dotenv()


def common_parser() -> ArgumentParser:
    parent_parser = ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--workdir",
        type=Path,
        default=Path(".") / ".rogue",
        help="Working directory",
    )
    parent_parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug logging",
    )
    parent_parser.add_argument(
        "--version",
        action="store_true",
        default=False,
        help="Show version",
    )
    parent_parser.add_argument(
        "--example",
        type=str,
        choices=[
            "tshirt_store",
            "tshirt_store_langgraph_mcp",
            "tshirt_store_chat_completions",
        ],
        help="Run with an example agent "
        "(e.g., tshirt_store, tshirt_store_langgraph_mcp, "
        "tshirt_store_chat_completions)",
    )
    parent_parser.add_argument(
        "--example-host",
        type=str,
        default="localhost",
        help="Host for the example agent (default: localhost)",
    )
    parent_parser.add_argument(
        "--example-port",
        type=int,
        default=10001,
        help="Port for the example agent (default: 10001)",
    )

    return parent_parser


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description="Rogue agent evaluator",
        parents=[common_parser()],
    )

    subparsers = parser.add_subparsers(dest="mode")

    # Server mode
    server_parser = subparsers.add_parser(
        "server",
        help="Run in server mode",
        parents=[common_parser()],
    )
    set_server_args(server_parser)

    # CLI mode
    cli_parser = subparsers.add_parser(
        "cli",
        help="Run in non-interactive CLI mode",
        parents=[common_parser()],
    )
    set_cli_args(cli_parser)

    # TUI mode
    tui_parser = subparsers.add_parser(
        "tui",
        help="Run the TUI binary directly",
        parents=[common_parser()],
    )
    tui_parser.add_argument(
        "--with-server",
        action="store_true",
        default=False,
        help="Start the rogue server alongside the TUI",
    )
    set_server_args(tui_parser)

    return parser.parse_args()


def start_example_agent(
    example_name: str,
    host: str,
    port: int,
) -> subprocess.Popen | None:
    """Start an example agent in a background subprocess."""
    logger.info(
        f"Starting example agent '{example_name}' on {host}:{port}...",
    )

    if example_name == "tshirt_store":
        # Use subprocess to run the example agent
        cmd = [
            sys.executable,
            "-m",
            "examples.tshirt_store_agent",
            "--host",
            host,
            "--port",
            str(port),
        ]
    elif example_name == "tshirt_store_langgraph_mcp":
        # Use subprocess to run the example agent
        cmd = [
            sys.executable,
            "-m",
            "examples.mcp.tshirt_store_langgraph_mcp",
            "--host",
            host,
            "--port",
            str(port),
            "--transport",
            "streamable-http",
        ]
    elif example_name == "tshirt_store_chat_completions":
        # Use subprocess to run the example agent
        cmd = [
            sys.executable,
            "-m",
            "examples.openai_api.chat_completions_agent",
            "--host",
            host,
            "--port",
            str(port),
        ]
    else:
        logger.error(f"Unknown example: {example_name}")
        return None

    try:
        process = subprocess.Popen(  # nosec: B603
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Give it a moment to start
        time.sleep(2)

        # Check if it's still running
        if process.poll() is None:
            logger.info(
                f"Example agent '{example_name}' started successfully at "
                f"http://{host}:{port}",
            )
            return process
        else:
            stdout, stderr = process.communicate()
            logger.error(
                f"Failed to start example agent '{example_name}'. "
                f"Exit code: {process.returncode}",
            )
            if stderr:
                logger.error(f"Error output: {stderr.decode()}")
            return None
    except Exception as e:
        logger.error(
            f"Failed to start example agent '{example_name}': {e}",
        )
        return None


def main() -> None:
    check_for_updates(__version__)
    args = parse_args()

    if args.version:
        print(f"Rogue AI version: {__version__}")
        sys.exit(0)

    tui_mode = args.mode == "tui" or args.mode is None

    log_file_path: Path | None = None
    if tui_mode:
        log_file_path = platformdirs.user_log_path(appname="rogue") / "rogue.log"
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        log_file_path = log_file_path.resolve()

    configure_logger(args.debug, file_path=log_file_path)

    # Start example agent if requested
    example_process = None
    if args.example:
        example_process = start_example_agent(
            args.example,
            args.example_host,
            args.example_port,
        )
        if not example_process:
            logger.error("Failed to start example agent. Exiting.")
            sys.exit(1)

    # Handle default behavior (no mode specified)
    if args.mode is None:
        # Default behavior: install TUI, start server, run TUI
        logger.info("Starting rogue-ai...")

        # Step 1: Install rogue-tui if needed
        if not RogueTuiInstaller().install_rogue_tui():
            logger.error("Failed to install rogue-tui. Exiting.")
            if example_process:
                example_process.terminate()
                example_process.wait()
            sys.exit(1)

        server_process = run_server(
            args,
            background=True,
            log_file=log_file_path,
        )

        # Step 2: Start the server in background
        if not server_process:
            logger.error("Failed to start rogue server. Exiting.")
            if example_process:
                example_process.terminate()
                example_process.wait()
            sys.exit(1)

        # Step 3: Run the TUI
        try:
            exit_code = run_rogue_tui()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Exiting.")
            exit_code = 0
        finally:
            server_process.terminate()
            server_process.join()
            if example_process:
                example_process.terminate()
                example_process.wait()
        sys.exit(exit_code)

    # Handle regular modes (ui, cli, server, tui)
    args.workdir.mkdir(exist_ok=True, parents=True)

    try:
        if args.mode == "server":
            run_server(args, background=False)
        elif args.mode == "cli":
            exit_code = asyncio.run(run_cli(args))
            sys.exit(exit_code)
        elif args.mode == "tui":
            if not RogueTuiInstaller().install_rogue_tui():
                logger.error("Failed to install rogue-tui. Exiting.")
                sys.exit(1)

            server_process = None
            if args.with_server:
                server_process = run_server(
                    args,
                    background=True,
                    log_file=log_file_path,
                )
                if not server_process:
                    logger.error("Failed to start rogue server. Exiting.")
                    sys.exit(1)

            try:
                exit_code = run_rogue_tui()
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received. Exiting.")
                exit_code = 0
            finally:
                if server_process:
                    server_process.terminate()
                    server_process.join()
            sys.exit(exit_code)
        else:
            raise ValueError(f"Unknown mode: {args.mode}")
    finally:
        # Clean up example agent if it was started
        if example_process:
            example_process.terminate()
            example_process.wait()


if __name__ == "__main__":
    main()
