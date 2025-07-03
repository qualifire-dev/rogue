from argparse import ArgumentParser, Namespace
from pathlib import Path

from .ui.app import get_app


def set_ui_args(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--port",
        type=int,
        help="Port to run the UI on",
    )
    parser.add_argument(
        "--workdir",
        type=Path,
        default=Path.home() / ".rogue",
        help="Working directory",
    )


def run_ui(args: Namespace) -> None:
    port: int | None = args.port
    workdir: Path = args.workdir

    workdir.mkdir(parents=True, exist_ok=True)

    app = get_app(workdir)
    app.launch(
        inbrowser=True,
        prevent_thread_lock=False,  # This might need to change after agent is created
        server_port=port,
    )
