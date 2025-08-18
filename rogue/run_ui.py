from argparse import ArgumentParser, Namespace
from pathlib import Path

from .ui.app import get_app


def set_ui_args(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--rogue-server-url",
        default="http://localhost:8000",
        help="Rogue server URL",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to run the UI on",
    )


def run_ui(args: Namespace) -> None:
    port: int | None = args.port
    workdir: Path = args.workdir
    rogue_server_url: str = args.rogue_server_url

    app = get_app(
        workdir,
        rogue_server_url,
    )
    app.launch(
        inbrowser=True,
        prevent_thread_lock=False,  # This might need to change after agent is created
        server_port=port,
    )
