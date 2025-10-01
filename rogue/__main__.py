import asyncio
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

import platformdirs
from dotenv import load_dotenv
from loguru import logger

from .common.logging.config import configure_logger
from .common.tui_installer import RogueTuiInstaller
from .common.update_checker import check_for_updates
from .run_cli import run_cli, set_cli_args
from .run_server import run_server, set_server_args
from .run_tui import run_rogue_tui
from .run_ui import run_ui, set_ui_args
from . import __version__


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

    # UI mode
    ui_parser = subparsers.add_parser(
        "ui",
        help="Run in interactive UI mode",
        parents=[common_parser()],
    )
    set_ui_args(ui_parser)

    # CLI mode
    cli_parser = subparsers.add_parser(
        "cli",
        help="Run in non-interactive CLI mode",
        parents=[common_parser()],
    )
    set_cli_args(cli_parser)

    # TUI mode
    subparsers.add_parser(
        "tui",
        help="Run the TUI binary directly",
        parents=[common_parser()],
    )

    return parser.parse_args()


def main() -> None:
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

    # Handle default behavior (no mode specified)
    if args.mode is None:
        # Default behavior: install TUI, start server, run TUI
        logger.info("Starting rogue-ai...")

        # Step 1: Install rogue-tui if needed
        if not RogueTuiInstaller().install_rogue_tui():
            logger.error("Failed to install rogue-tui. Exiting.")
            sys.exit(1)

        server_process = run_server(
            args,
            background=True,
            log_file=log_file_path,
        )

        # Step 2: Start the server in background
        if not server_process:
            logger.error("Failed to start rogue server. Exiting.")
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
        sys.exit(exit_code)

    # Handle regular modes (ui, cli, server, tui)
    args.workdir.mkdir(exist_ok=True, parents=True)

    if args.mode == "ui":
        run_ui(args)
    elif args.mode == "server":
        run_server(args, background=False)
    elif args.mode == "cli":
        exit_code = asyncio.run(run_cli(args))
        sys.exit(exit_code)
    elif args.mode == "tui":
        if not RogueTuiInstaller().install_rogue_tui():
            logger.error("Failed to install rogue-tui. Exiting.")
            sys.exit(1)
        exit_code = run_rogue_tui()
        sys.exit(exit_code)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    check_for_updates(__version__)
    main()
