import asyncio
import sys
from argparse import ArgumentParser
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from .common.configure_logger import configure_logger
from .common.tui_installer import RogueTuiInstaller
from .run_cli import run_cli, set_cli_args
from .run_server import run_server, set_server_args
from .run_tui import run_rogue_tui
from .run_ui import run_ui, set_ui_args

load_dotenv()


def common_parser():
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
    return parent_parser


def parse_args():
    parser = ArgumentParser(
        description="Rogue agent evaluator",
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


def main():
    args = parse_args()

    # Handle default behavior (no mode specified)
    if args.mode is None:
        # Default behavior: install TUI, start server, run TUI
        logger.info("Starting rogue-ai...")

        # Step 1: Install rogue-tui if needed
        if not RogueTuiInstaller().install_rogue_tui():
            logger.error("Failed to install rogue-tui. Exiting.")
            sys.exit(1)

        # Step 2: Start the server in background
        if not run_server(args, background=True):
            logger.error("Failed to start rogue server. Exiting.")
            sys.exit(1)

        # Step 3: Run the TUI
        exit_code = run_rogue_tui()
        sys.exit(exit_code)

    # Handle regular modes (ui, cli, server, tui)
    configure_logger(args.debug)
    args.workdir.mkdir(exist_ok=True, parents=True)

    if args.mode == "ui":
        run_ui(args)
    elif args.mode == "cli":
        exit_code = asyncio.run(run_cli(args))
        sys.exit(exit_code)
    elif args.mode == "server":
        success = run_server(args, background=False)
        sys.exit(0 if success else 1)
    elif args.mode == "tui":
        exit_code = run_rogue_tui()
        sys.exit(exit_code)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
