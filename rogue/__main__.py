import asyncio
import json
import subprocess  # nosec: B404
import sys
from argparse import ArgumentParser, Namespace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import platformdirs
import requests
from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

from .common.logging.config import configure_logger
from .common.tui_installer import RogueTuiInstaller
from .run_cli import run_cli, set_cli_args
from .run_server import run_server, set_server_args
from .run_tui import run_rogue_tui
from .run_ui import run_ui, set_ui_args
from . import __version__


load_dotenv()


def common_parser() -> ArgumentParser:
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
    parent_parser.add_argument(
        "--version",
        action="store_true",
        default=False,
        help="Show version",
    )

    return parent_parser


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description="Rogue agent evaluator",
        parents=[common_parser()],
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

    # TUI mode
    subparsers.add_parser(
        "tui",
        help="Run the TUI binary directly",
        parents=[common_parser()],
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.version:
        print(f"Rogue AI version: {__version__}")
        sys.exit(0)

    tui_mode = args.mode == "tui" or args.mode is None

    log_file_path: Path | None = None
    if tui_mode:
        log_file_path = platformdirs.user_log_path(appname="rogue") / "rogue.log"
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        log_file_path = log_file_path.resolve()

    configure_logger(args.debug, file_path=log_file_path)

    # Handle default behavior (no mode specified)
    if args.mode is None:
        # Default behavior: install TUI, start server, run TUI
        logger.info("Starting rogue-ai...")

        # Step 1: Install rogue-tui if needed
        if not RogueTuiInstaller().install_rogue_tui():
            logger.error("Failed to install rogue-tui. Exiting.")
            sys.exit(1)

        server_process = run_server(
            args,
            background=True,
            log_file=log_file_path,
        )

        # Step 2: Start the server in background
        if not server_process:
            logger.error("Failed to start rogue server. Exiting.")
            sys.exit(1)

        # Step 3: Run the TUI
        try:
            exit_code = run_rogue_tui()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Exiting.")
            exit_code = 0
        finally:
            server_process.terminate()
            server_process.join()
        sys.exit(exit_code)

    # Handle regular modes (ui, cli, server, tui)
    args.workdir.mkdir(exist_ok=True, parents=True)

    if args.mode == "ui":
        run_ui(args)
    elif args.mode == "server":
        run_server(args, background=False)
    elif args.mode == "cli":
        exit_code = asyncio.run(run_cli(args))
        sys.exit(exit_code)
    elif args.mode == "tui":
        if not RogueTuiInstaller().install_rogue_tui():
            logger.error("Failed to install rogue-tui. Exiting.")
            sys.exit(1)
        exit_code = run_rogue_tui()
        sys.exit(exit_code)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")


def check_for_updates() -> None:
    """
    Check for available updates and prompt user if a newer version is available.
    Similar to oh-my-zsh update experience.
    """
    try:
        # Don't check for updates if we've checked recently
        cache_info = _get_update_cache()
        if _should_skip_update_check(cache_info):
            return

        # Get latest version from PyPI
        latest_version = _get_latest_version_from_pypi()
        if not latest_version:
            return

        # Save the check info
        _save_update_cache(latest_version)

        # Compare versions and show update prompt if needed
        if _is_newer_version(latest_version, __version__):
            _show_update_prompt(latest_version)
    except Exception:
        # Silently handle any errors - update checking shouldn't break the app
        logger.debug("Error checking for updates", exc_info=True)


def _get_update_cache() -> Dict[str, Any]:
    """Get cached update information."""
    cache_file = platformdirs.user_cache_path(appname="rogue") / "update_cache.json"

    if not cache_file.exists():
        return {}

    try:
        with open(cache_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _should_skip_update_check(cache_info: Dict[str, Any]) -> bool:
    """Check if we should skip the update check based on cache."""
    if not cache_info:
        return False

    last_check = cache_info.get("last_check")
    if not last_check:
        return False

    # Skip if we've checked in the last 24 hours
    last_check_time = datetime.fromisoformat(last_check)
    return datetime.now() - last_check_time < timedelta(hours=24)


def _get_latest_version_from_pypi() -> Optional[str]:
    """Fetch the latest version from PyPI."""
    try:
        response = requests.get(
            "https://pypi.org/pypi/rogue-ai/json",
            timeout=5,
            headers={"User-Agent": f"rogue-ai/{__version__}"},
        )
        response.raise_for_status()

        data = response.json()
        return data["info"]["version"]
    except (requests.RequestException, KeyError, json.JSONDecodeError):
        return None


def _save_update_cache(latest_version: str) -> None:
    """Save update check information to cache."""
    cache_file = platformdirs.user_cache_path(appname="rogue") / "update_cache.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    cache_data = {
        "last_check": datetime.now().isoformat(),
        "latest_version": latest_version,
        "current_version": __version__,
    }

    try:
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)
    except IOError:
        pass  # Silently handle write errors


def _is_newer_version(latest: str, current: str) -> bool:
    """Compare version strings to determine if latest is newer than current."""

    def version_tuple(v: str) -> tuple:
        """Convert version string to tuple for comparison."""
        try:
            return tuple(map(int, v.split(".")))
        except ValueError:
            # Handle non-standard version formats gracefully
            return (0, 0, 0)

    return version_tuple(latest) > version_tuple(current)


def _show_update_prompt(latest_version: str) -> None:
    """Display the update prompt with rich formatting and interactive option."""
    console = Console()

    # Create the update message
    title = Text("🚀 Update Available!", style="bold yellow")

    content = Text()
    content.append("A new version of rogue-ai is available!\n\n", style="")
    content.append("Current version: ", style="dim")
    content.append(f"{__version__}\n", style="red")
    content.append("Latest version:  ", style="dim")
    content.append(f"{latest_version}\n\n", style="green bold")
    content.append("To update manually, run: ", style="dim")
    content.append("uv tool upgrade rogue-ai", style="cyan bold")
    content.append(" or ", style="dim")
    content.append("uvx --refresh rogue-ai", style="cyan bold")

    # Create a panel with the update message
    panel = Panel(
        content,
        title=title,
        border_style="yellow",
        padding=(1, 2),
    )

    # Print with some spacing
    console.print()
    console.print(panel)

    # Ask user if they want to update now
    try:
        should_update = Confirm.ask(
            "[bold cyan]Would you like to update now?[/bold cyan]",
            default=True,
        )

        if should_update:
            _run_update_command()
        else:
            console.print(
                "[dim]Update skipped. Run 'uv tool upgrade rogue-ai' or "
                "'uvx --refresh rogue-ai' later to update.[/dim]",
            )
    except (KeyboardInterrupt, EOFError):
        # Handle Ctrl+C or input interruption gracefully
        console.print("\n[dim]Update skipped.[/dim]")

    console.print()


def _run_update_command() -> None:
    """Execute the appropriate update command based on installation method."""
    console = Console()

    try:
        console.print("[yellow]Updating rogue-ai...[/yellow]")
        console.print(
            "[dim]This may take a few minutes to download and install "
            "dependencies...[/dim]",
        )

        # First, try to upgrade using uv tool
        # (for users who installed with uv tool install)
        result = subprocess.run(
            ["uv", "tool", "install", "-U", "rogue-ai"],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout for the update
        )  # nosec: B607 B603

        # If that fails because it's not installed as a tool, try uvx method
        if result.returncode != 0 and "is not installed" in result.stderr:
            console.print("[dim]Trying alternative update method...[/dim]")
            # For uvx installations, we need to reinstall
            result = subprocess.run(  # nosec: B607 B603
                ["uvx", "--refresh", "rogue-ai", "--version"],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout for the update
            )

        if result.returncode == 0:
            # install TUI
            RogueTuiInstaller().install_rogue_tui(
                upgrade=True,
            )

            console.print("[bold green]✅ Update completed successfully![/bold green]")
            console.print(
                "[dim]Restart any running rogue-ai processes to use the "
                "new version.[/dim]",
            )
        else:
            console.print("[bold red]❌ Update failed![/bold red]")
            if result.stderr:
                console.print(f"[red]Error: {result.stderr.strip()}[/red]")
            console.print(
                "[dim]Please try running 'uv tool upgrade rogue-ai' or "
                "'uvx --refresh rogue-ai' manually.[/dim]",
            )
    except subprocess.TimeoutExpired:
        console.print("[bold red]❌ Update timed out after 10 minutes![/bold red]")
        console.print(
            "[dim]This may indicate a network issue. Please try running "
            "'uv tool upgrade rogue-ai' or 'uvx --refresh rogue-ai' manually.[/dim]",
        )
    except FileNotFoundError:
        console.print("[bold red]❌ uv command not found![/bold red]")
        console.print("[dim]Please ensure uv is installed and in your PATH.[/dim]")
    except Exception as e:
        console.print(f"[bold red]❌ Update failed: {e}[/bold red]")
        console.print(
            "[dim]Please try running 'uv tool upgrade rogue-ai' or "
            "'uvx --refresh rogue-ai' manually.[/dim]",
        )


if __name__ == "__main__":
    check_for_updates()
    main()
