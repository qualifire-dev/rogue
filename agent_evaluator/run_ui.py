from pathlib import Path

from .ui.app import get_app


def run_ui(
    port: int | None,
    workdir: str | None,
):
    if workdir:
        workdir_path = Path(workdir)
    else:
        workdir_path = Path.home() / ".qualifire" / "agent_evaluator_runs"

    workdir_path.mkdir(parents=True, exist_ok=True)

    app = get_app(workdir_path)
    app.launch(
        inbrowser=True,
        prevent_thread_lock=False,  # This might need to change after we create the agent
        server_port=port,
    )
