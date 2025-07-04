from argparse import ArgumentParser
from pathlib import Path

from dotenv import load_dotenv

from .common.configure_logger import configure_logger
from .run_cli import run_cli, set_cli_args
from .run_ui import run_ui, set_ui_args

load_dotenv()


def parse_args():
    parser = ArgumentParser(description="Rouge agent evaluator")

    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path(".") / ".rogue",
        help="Working directory",
    )

    subparsers = parser.add_subparsers(dest="mode")

    # UI mode
    ui_parser = subparsers.add_parser(
        "ui",
        help="Run in interactive UI mode",
    )
    set_ui_args(ui_parser)

    # CLI mode
    cli_parser = subparsers.add_parser(
        "cli",
        help="Run in non-interactive CLI mode",
    )
    set_cli_args(cli_parser)

    args, unknown = parser.parse_known_args()

    # Default to UI mode if no subcommand is provided
    if args.mode is None:
        # Parse again, but this time with defaulting to "ui"
        args = parser.parse_args(["ui"] + unknown)

    return args


def main():
    configure_logger()
    args = parse_args()

    args.workdir.mkdir(exist_ok=True, parents=True)

    if args.mode == "ui":
        run_ui(args)
    elif args.mode == "cli":
        run_cli(args)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
