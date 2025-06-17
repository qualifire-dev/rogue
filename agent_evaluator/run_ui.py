from pathlib import Path

from .ui.app import get_app


def run_ui(
    port: int | None,
    workdir: Path,
):
    workdir.mkdir(parents=True, exist_ok=True)

    app = get_app(workdir)
    app.launch(
        inbrowser=True,
        prevent_thread_lock=False,  # This might need to change after we create the agent
        server_port=port,
    )
