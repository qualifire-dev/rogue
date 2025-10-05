"""TUI installer module for downloading and installing rogue-tui binary."""

import os
import platform
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Optional

import platformdirs
import requests
from loguru import logger
from rich.console import Console


class RogueTuiInstaller:
    def __init__(self, repo: str = "qualifire-dev/rogue"):
        self._repo = repo
        self._github_token = os.getenv("GITHUB_TOKEN")
        self._headers = (
            {"Authorization": f"Bearer {self._github_token}"}
            if self._github_token
            else {}
        )

    @property
    @lru_cache(1)
    def _architecture(self) -> str:
        """Get the system architecture in a format suitable for GitHub releases."""
        arch = platform.machine().lower()
        if arch in ["x86_64", "amd64"]:
            return "amd64"
        elif arch in ["aarch64", "arm64"]:
            return "arm64"
        else:
            return arch

    @property
    @lru_cache(1)
    def _os(self) -> str:
        """Get the operating system name."""
        return platform.system().lower()

    def _get_latest_github_release(self) -> Optional[dict]:
        """Get the latest release information from GitHub."""
        console = Console()

        try:
            url = f"https://api.github.com/repos/{self._repo}/releases/latest"

            with console.status(
                "[bold blue]Fetching latest release information...",
                spinner="dots",
            ):
                response = requests.get(
                    url,
                    timeout=10,
                    headers=self._headers,
                )
                response.raise_for_status()
                return response.json()
        except Exception:
            logger.exception("Error fetching latest release")
            return None

    def _find_asset_for_platform(
        self,
        release_data: dict,
    ) -> Optional[str]:
        """Find the appropriate asset for the current platform."""
        if not release_data or "assets" not in release_data:
            return None

        binary_name = f"rogue-tui-{self._os}-{self._architecture}"
        if self._os == "windows":
            binary_name += ".exe"

        for asset in release_data["assets"]:
            asset_name = asset["name"].lower()
            if binary_name.lower() in asset_name:
                return asset["url"]

        return None

    def _download_rogue_tui_to_temp(self) -> str:
        console = Console()

        # Get latest release
        release_data = self._get_latest_github_release()
        if not release_data:
            raise Exception("Failed to fetch latest release information.")

        # Find appropriate asset
        download_url = self._find_asset_for_platform(release_data)
        if not download_url:
            logger.error(
                f"No suitable binary found for {self._os}-{self._architecture}.",
                extra={"available_assets": release_data["assets"]},
            )
            raise Exception("No suitable binary found for current platform.")

        # Show spinner during download
        with console.status(
            "[bold green]Downloading rogue-tui binary...",
            spinner="dots",
        ):
            response = requests.get(
                download_url,
                timeout=60,
                headers={
                    "Accept": "application/octet-stream",
                    **self._headers,
                },
            )
            response.raise_for_status()

            # Create a temporary file
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix="-rogue-tui",
            ) as tmp_file:
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

        # Make it executable
        os.chmod(tmp_path, 0o755)  # nosec: B103

        return tmp_path

    def _get_install_path(self) -> Path:
        install_path = Path.home()
        if self._os == "windows":
            install_path = (
                Path(platformdirs.user_data_dir("rogue")) / "bin" / "rogue-tui.exe"
            )
        else:
            install_path = Path.home() / ".local" / "bin" / "rogue-tui"

        install_path.parent.mkdir(parents=True, exist_ok=True)

        return install_path

    def _handle_path_env(self, install_dir: Path) -> None:
        sep = ":"
        if self._os == "windows":
            sep = ";"

        if str(install_dir) not in os.environ.get("PATH", "").split(sep):
            os.environ["PATH"] += sep + str(install_dir)
            # TODO update shellrc file to update the path

    def _is_rogue_tui_installed(self) -> bool:
        sep = ":"
        if self._os == "windows":
            sep = ";"

        tui_from_path = shutil.which("rogue-tui")
        tui_from_install_path = self._get_install_path()
        if tui_from_path:
            return True
        elif tui_from_install_path.is_file():
            os.environ["PATH"] += sep + str(tui_from_install_path.parent)
            return True
        else:
            return False

    def install_rogue_tui(
        self,
        upgrade: bool = False,
    ) -> bool:
        """Install rogue-tui from GitHub releases if not already installed."""
        console = Console()
        # Check if rogue-tui is already available
        if self._is_rogue_tui_installed() and not upgrade:
            console.print("[green]✅ rogue-tui is already installed.[/green]")
            return True

        console.print(
            "[yellow]📦 Installing rogue-tui from GitHub releases...[/yellow]",
        )

        try:
            tmp_path = self._download_rogue_tui_to_temp()
        except Exception:
            console.print("[red]❌ Failed to download rogue-tui.[/red]")
            logger.exception("Failed to download rogue-tui.")
            return False

        try:
            # Move to final location
            install_path = self._get_install_path()

            with console.status("[bold yellow]Installing rogue-tui...", spinner="dots"):
                shutil.move(tmp_path, install_path)
        except Exception:
            console.print("[red]❌ Failed to install rogue-tui.[/red]")
            logger.exception("Failed to install rogue-tui.")
            return False

        self._handle_path_env(install_path.parent)

        console.print("[green]✅ rogue-tui installed successfully![/green]")
        # logger.debug(f"rogue-tui installed to {install_path}")
        return True
