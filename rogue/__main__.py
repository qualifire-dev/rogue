import asyncio
import sys
from argparse import ArgumentParser
from pathlib import Path

from dotenv import load_dotenv

from .common.configure_logger import configure_logger
from .run_cli import run_cli, set_cli_args
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
        description="Rouge agent evaluator",
        parents=[common_parser()],
    )

    subparsers = parser.add_subparsers(dest="mode")

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

    args, unknown = parser.parse_known_args()

    # Default to UI mode if no subcommand is provided
    if args.mode is None:
        # Parse again, but this time with defaulting to "ui"
        args = parser.parse_args(["ui"] + unknown)

    return args


def main():
    args = parse_args()
    configure_logger(args.debug)

    args.workdir.mkdir(exist_ok=True, parents=True)

    if args.mode == "ui":
        run_ui(args)
    elif args.mode == "cli":
        exit_code = asyncio.run(run_cli(args))
        sys.exit(exit_code)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
