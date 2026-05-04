import contextlib
import os
import time
import webbrowser
from argparse import ArgumentParser, Namespace
from pathlib import Path

from loguru import logger

from .run_server import run_server, set_server_args


def set_web_args(parser: ArgumentParser) -> None:
    set_server_args(parser)
    parser.add_argument(
        "--no-browser",
        action="store_true",
        default=False,
        help="Do not open a browser window automatically.",
    )
    parser.add_argument(
        "--server-url",
        default=None,
        help=(
            "Point the SPA at a remote API instead of starting a local one. "
            "When set, no local server is started."
        ),
    )


def web_dist_path() -> Path:
    """Filesystem location of the bundled SPA.

    Resolves in this order:
    1. ``rogue/web_dist/`` next to this file (the layout produced by the wheel
       force-include — the canonical location for installed users).
    2. ``packages/web/dist/`` walking up from this file (the layout used during
       editable / source installs, so ``uv run python -m rogue web`` works
       without copying the build artifact into the package tree).
    """
    bundled = Path(__file__).resolve().parent / "web_dist"
    if (bundled / "index.html").is_file():
        return bundled
    # Walk up to the repo root looking for packages/web/dist
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "packages" / "web" / "dist"
        if (candidate / "index.html").is_file():
            return candidate
    return bundled


def run_web(args: Namespace) -> int:
    """Start the FastAPI server (which serves the SPA) and open a browser."""

    dist = web_dist_path()
    if not args.server_url and not (dist / "index.html").is_file():
        logger.error(
            "Web assets are missing from the installed package. "
            "Either reinstall rogue-ai (the published wheel includes the SPA), "
            "or build it locally: `cd packages/web && pnpm install && pnpm build`.",
        )
        return 1

    server_proc = None
    if not args.server_url:
        try:
            server_proc = run_server(args, background=True)
        except Exception as e:
            logger.error(f"Failed to start rogue server: {e}")
            return 1
        if server_proc is None:
            logger.error("Failed to start rogue server.")
            return 1

    host = getattr(args, "host", os.getenv("HOST", "127.0.0.1"))
    port = getattr(args, "port", int(os.getenv("PORT", "8000")))
    url = args.server_url or f"http://{host}:{port}/"

    if not args.no_browser:
        # Headless envs may not have a browser — best effort only.
        with contextlib.suppress(Exception):
            webbrowser.open(url)

    logger.info(f"Rogue web UI: {url}  (Ctrl-C to quit)")

    try:
        while True:
            if server_proc is not None and not server_proc.is_alive():
                logger.error("Rogue server process exited unexpectedly.")
                return 1
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Exiting.")
        return 0
    finally:
        if server_proc is not None:
            server_proc.terminate()
            server_proc.join()
