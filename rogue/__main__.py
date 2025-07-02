from argparse import ArgumentParser
from pathlib import Path

from dotenv import load_dotenv

from .common.configure_logger import configure_logger
from .run_cli import run_cli
from .run_ui import run_ui

load_dotenv()


def parse_args():
    parser = ArgumentParser(description="Rouge agent evaluator")

    subparsers = parser.add_subparsers(dest="mode")

    # UI mode
    ui_parser = subparsers.add_parser(
        "ui",
        help="Run in interactive UI mode",
    )
    ui_parser.add_argument(
        "--port",
        type=int,
        help="Port to run the UI on",
    )
    ui_parser.add_argument(
        "--workdir",
        type=Path,
        default=Path.home() / ".rogue",
        help="Working directory",
    )

    # CLI mode
    cli_parser = subparsers.add_parser(
        "cli",
        help="Run in non-interactive CLI mode",
    )
    cli_parser.add_argument(
        "--evaluated-agent-url",
        required=True,
        help="URL of the agent to evaluate",
    )
    cli_parser.add_argument(
        "--input-scenarios-file",
        required=True,
        help="Path to input scenarios file",
    )
    cli_parser.add_argument(
        "--output-report-file",
        required=True,
        help="Path to output report file",
    )

    args, unknown = parser.parse_known_args()

    # Default to UI mode if no subcommand is provided
    if args.mode is None:
        # Parse again, but this time with defaulting to "ui"
        args = parser.parse_args(["ui"] + unknown)

    return args


def main():
    configure_logger()
    args = parse_args()

    if args.mode == "ui":
        run_ui(args.port, args.workdir)
    elif args.mode == "cli":
        run_cli(
            args.evaluated_agent_url,
            args.input_scenarios_file,
            args.output_report_file,
        )
    else:
        raise ValueError(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
