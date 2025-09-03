import asyncio
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

from .common.configure_logger import configure_logger
from .run_cli import run_cli, set_cli_args
from .run_server import set_server_args
from .run_ui import run_ui, set_ui_args

load_dotenv()


def get_architecture() -> str:
    """Get the system architecture in a format suitable for GitHub releases."""
    arch = platform.machine().lower()
    if arch in ["x86_64", "amd64"]:
        return "amd64"
    elif arch in ["aarch64", "arm64"]:
        return "arm64"
    elif arch in ["armv7l"]:
        return "armv7"
    else:
        return arch


def get_os() -> str:
    """Get the operating system name."""
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        return system


def is_rogue_server_running(host: str = "127.0.0.1", port: int = 8000) -> bool:
    """Check if the rogue server is running by making a health check request."""
    try:
        response = requests.get(f"http://{host}:{port}/api/v1/health", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def get_latest_github_release(repo: str) -> Optional[dict]:
    """Get the latest release information from GitHub."""
    try:
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching latest release: {e}")
        return None


def find_asset_for_platform(
    release_data: dict,
    os_name: str,
    arch: str,
) -> Optional[str]:
    """Find the appropriate asset for the current platform."""
    if not release_data or "assets" not in release_data:
        return None

    # Common patterns for binary names
    patterns = [
        f"rogue-tui-{os_name}-{arch}",
        f"rogue-tui_{os_name}_{arch}",
        f"rogue-tui-{arch}-{os_name}",
        f"rogue-tui_{arch}_{os_name}",
    ]
    if os_name == "windows":
        patterns.append(f"rogue-tui-{os_name}-{arch}.exe")

    for asset in release_data["assets"]:
        asset_name = asset["name"].lower()
        for pattern in patterns:
            if pattern.lower() in asset_name:
                return asset["browser_download_url"]

    return None


def install_rogue_tui() -> bool:
    """Install rogue-tui from GitHub releases if not already installed."""
    # Check if rogue-tui is already available
    if shutil.which("rogue-tui"):
        print("rogue-tui is already installed.")
        return True

    print("rogue-tui not found. Installing from GitHub releases...")

    # Get platform information
    os_name = get_os()
    arch = get_architecture()

    print(f"Detected platform: {os_name}-{arch}")

    # Get latest release
    release_data = get_latest_github_release("qualifire-dev/rogue-ai")
    if not release_data:
        print("Failed to fetch latest release information.")
        return False

    # Find appropriate asset
    download_url = find_asset_for_platform(release_data, os_name, arch)
    if not download_url:
        print(f"No suitable binary found for {os_name}-{arch}")
        print("Available assets:")
        for asset in release_data.get("assets", []):
            print(f"  - {asset['name']}")
        return False

    print(f"Downloading: {download_url}")

    try:
        # Download the binary
        response = requests.get(download_url, timeout=60)
        response.raise_for_status()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix="-rogue-tui") as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name

        # Make it executable
        os.chmod(tmp_path, 0o755)

        # Determine installation directory
        if os_name == "windows":
            install_dir = (
                Path.home()
                / "AppData"
                / "Local"
                / "Microsoft"
                / "WinGet"
                / "Packages"
                / "rogue-tui"
            )
            install_dir.mkdir(parents=True, exist_ok=True)
            install_path = install_dir / "rogue-tui.exe"
        else:
            # Try to install to a user-accessible location
            install_dir = Path.home() / ".local" / "bin"
            install_dir.mkdir(parents=True, exist_ok=True)
            install_path = install_dir / "rogue-tui"

        # Move to final location
        shutil.move(tmp_path, install_path)

        # Add to PATH if not already there
        if str(install_dir) not in os.environ.get("PATH", ""):
            print(f"Please add {install_dir} to your PATH environment variable.")
            print("Add this line to your shell profile:")
            print(f'export PATH="$PATH:{install_dir}"')

        print(f"rogue-tui installed successfully to {install_path}")
        return True

    except Exception as e:
        print(f"Failed to install rogue-tui: {e}")
        return False


def start_rogue_server_background(host: str = "127.0.0.1", port: int = 8000) -> bool:
    """Start the rogue server in background if not already running."""
    # Check if server is already running
    if is_rogue_server_running(host, port):
        print("Rogue server is already running.")
        return True

    print("Starting rogue server...")

    try:
        # Start server in background
        cmd = [
            sys.executable,
            "-m",
            "rogue",
            "server",
            "--host",
            host,
            "--port",
            str(port),
        ]
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # Wait a moment and check if it started successfully
        time.sleep(3)
        if is_rogue_server_running(host, port):
            print(f"Rogue server started on {host}:{port}")
            return True
        else:
            print("Failed to start rogue server.")
            return False

    except Exception as e:
        print(f"Error starting rogue server: {e}")
        return False


def run_rogue_tui() -> int:
    """Run the rogue TUI binary."""
    print("Running rogue TUI...")

    try:
        # Find the rogue-tui binary
        tui_path = shutil.which("rogue-tui")
        if not tui_path:
            print("rogue-tui not found. Please install it first.")
            return 1

        # Run the TUI with proper stdin/stdout handling
        result = subprocess.run([tui_path])
        return result.returncode

    except Exception as e:
        print(f"Error running rogue TUI: {e}")
        return 1


def common_parser():
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
    return parent_parser


def parse_args():
    parser = ArgumentParser(
        description="Rogue agent evaluator",
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


def main():
    args = parse_args()

    # Handle default behavior (no mode specified)
    if args.mode is None:
        # Default behavior: install TUI, start server, run TUI
        print("Starting rogue-ai in default mode...")

        # Step 1: Install rogue-tui if needed
        if not install_rogue_tui():
            print("Failed to install rogue-tui. Exiting.")
            sys.exit(1)

        # Step 2: Start the server in background
        if not start_rogue_server_background():
            print("Failed to start rogue server. Exiting.")
            sys.exit(1)

        # Step 3: Run the TUI
        exit_code = run_rogue_tui()
        sys.exit(exit_code)

    # Handle regular modes (ui, cli, server, tui)
    configure_logger(args.debug)
    args.workdir.mkdir(exist_ok=True, parents=True)

    if args.mode == "ui":
        run_ui(args)
    elif args.mode == "cli":
        exit_code = asyncio.run(run_cli(args))
        sys.exit(exit_code)
    elif args.mode == "server":
        # Start server in background (uvx mode)
        success = start_rogue_server_background(args.host, args.port)
        sys.exit(0 if success else 1)
    elif args.mode == "tui":
        # Run TUI directly
        exit_code = run_rogue_tui()
        sys.exit(exit_code)
    else:
        raise ValueError(f"Unknown mode: {args.mode}")


if __name__ == "__main__":
    main()
