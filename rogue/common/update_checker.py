"""
Update checking and automatic update functionality for Rogue.

This module provides oh-my-zsh style update prompts that check PyPI for newer
versions and allow users to update immediately.
"""

import json
import shutil
import subprocess  # nosec: B404
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import platformdirs
import requests
from loguru import logger
from packaging import version
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

from ..common.tui_installer import RogueTuiInstaller


def check_for_updates(current_version: str) -> None:
    """
    Check for available updates and prompt user if a newer version is available.
    Similar to oh-my-zsh update experience.

    Args:
        current_version: The current version of the application
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
        _save_update_cache(latest_version, current_version)

        # Compare versions and show update prompt if needed
        if _is_newer_version(latest_version, current_version):
            _show_update_prompt(latest_version, current_version)

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

    # Skip if we've checked in the last 10 minutes
    last_check_time = datetime.fromisoformat(last_check)
    return datetime.now() - last_check_time < timedelta(minutes=10)


def _get_latest_version_from_pypi() -> Optional[str]:
    """Fetch the latest version from PyPI."""
    try:
        response = requests.get(
            "https://pypi.org/pypi/rogue-ai/json",
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()
        return data.get("info", {}).get("version")

    except Exception:
        return None


def _save_update_cache(latest_version: str, current_version: str) -> None:
    """Save update check information to cache."""
    cache_file = platformdirs.user_cache_path(appname="rogue") / "update_cache.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)

    cache_data = {
        "last_check": datetime.now().isoformat(),
        "latest_version": latest_version,
        "current_version": current_version,
    }

    try:
        with open(cache_file, "w") as f:
            json.dump(cache_data, f, indent=2)
    except IOError:
        pass  # Silently handle write errors


def _is_newer_version(latest: str, current: str) -> bool:
    """Compare version strings to determine if latest is newer than current."""
    try:
        return version.parse(latest) > version.parse(current)
    except version.InvalidVersion:
        # Handle non-standard version formats gracefully
        return False


def _show_update_prompt(latest_version: str, current_version: str) -> None:
    """Display the update prompt with rich formatting and interactive option."""
    console = Console()

    # Create the update message
    title = Text("🚀 Update Available!", style="bold yellow")

    content = Text()
    content.append("A new version of rogue-ai is available!\n\n", style="")
    content.append("Current version: ", style="dim")
    content.append(f"{current_version}\n", style="red")
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
            run_update_command()
        else:
            console.print(
                "[dim]Update skipped. Run 'uv tool upgrade rogue-ai' or "
                "'uvx --refresh rogue-ai' later to update.[/dim]",
            )
    except (KeyboardInterrupt, EOFError):
        # Handle Ctrl+C or input interruption gracefully
        console.print("\n[dim]Update skipped.[/dim]")

    console.print()


def run_update_command() -> None:
    """Execute the appropriate update command based on installation method."""
    console = Console()

    try:
        console.print(
            "[dim]This may take a few minutes to download and install "
            "dependencies...[/dim]",
        )

        if not shutil.which("uv"):
            console.print(
                "[dim]uv not found. please update manually using[/dim]"
                "[dim]- uv tool upgrade rogue-ai[/dim]"
                "[dim]or[/dim]"
                "[dim]- pip install rogue-ai -U[/dim]",
            )
            return

        with console.status("[yellow]Updating rogue-ai...[/yellow]", spinner="dots"):
            # First, try to upgrade using uv tool
            # (for users who installed with uv tool install)
            result = subprocess.run(  # nosec: B607 B603
                ["uv", "tool", "install", "-U", "rogue-ai"],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout for the update
            )

            # If that fails because it's not installed as a tool, try uvx method
            if result.returncode != 0 and "is not installed" in result.stderr:
                # For uvx installations, we need to reinstall
                result = subprocess.run(  # nosec: B607 B603
                    ["uvx", "--refresh", "rogue-ai", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10 minute timeout for the update
                )

            if result.returncode == 0:
                # Install TUI
                RogueTuiInstaller().install_rogue_tui(
                    upgrade=True,
                )

        if result.returncode == 0:
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
