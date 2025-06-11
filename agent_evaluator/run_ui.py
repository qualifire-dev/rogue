import tempfile
from pathlib import Path

from .ui.app import get_app


def run_ui(
    port: int | None,
    workdir: str | None,
):
    workdir = workdir or tempfile.mkdtemp()
    app = get_app(Path(workdir))
    app.launch(
        inbrowser=True,
        prevent_thread_lock=False,  # This might need to change after we create the agent
        server_port=port,
    )
