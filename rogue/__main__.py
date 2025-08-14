import asyncio
import sys
from argparse import ArgumentParser
from pathlib import Path

from dotenv import load_dotenv

from .common.configure_logger import configure_logger
from .run_cli import run_cli, set_cli_args
from .run_server import run_server, set_server_args
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

    # Inject 'ui' if no subcommand is present
    argv = sys.argv[1:]
    if len(argv) == 0 or argv[0] not in {"ui", "cli", "server"}:
        argv = ["ui"] + argv

    return parser.parse_args(argv)


def main():
    args = parse_args()
    configure_logger(args.debug)

    args.workdir.mkdir(exist_ok=True, parents=True)

    if args.mode == "ui":
        run_ui(args)
    elif args.mode == "cli":
        exit_code = asyncio.run(run_cli(args))
        sys.exit(exit_code)
    elif args.mode == "server":
        run_server(args)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
