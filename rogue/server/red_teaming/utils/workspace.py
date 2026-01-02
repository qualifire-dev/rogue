"""
Workspace utilities for red teaming.

Handles .rogue folder management for storing red team scan results,
CSV exports, and other artifacts.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from loguru import logger


def get_rogue_folder(workspace_path: Optional[str] = None) -> Path:
    """
    Get or create the .rogue folder for storing red team artifacts.

    Args:
        workspace_path: Optional workspace path. If None, uses current directory.

    Returns:
        Path to .rogue folder
    """
    if workspace_path:
        base_path = Path(workspace_path)
    else:
        base_path = Path.cwd()

    rogue_folder = base_path / ".rogue"

    # Create folder if it doesn't exist
    if not rogue_folder.exists():
        rogue_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created .rogue folder at {rogue_folder}")

    return rogue_folder


def generate_timestamped_filename(prefix: str, extension: str = "csv") -> str:
    """
    Generate a timestamped filename for exports.

    Args:
        prefix: Filename prefix (e.g., "red_team_conversations")
        extension: File extension (default: "csv")

    Returns:
        Timestamped filename (e.g., "red_team_conversations_20251201_143022.csv")
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def get_csv_export_paths(
    workspace_path: Optional[str] = None,
) -> Tuple[Path, Path]:
    """
    Get paths for CSV exports in .rogue folder.

    Args:
        workspace_path: Optional workspace path

    Returns:
        Tuple of (conversations_csv_path, summary_csv_path)
    """
    rogue_folder = get_rogue_folder(workspace_path)

    conversations_filename = generate_timestamped_filename("red_team_conversations")
    summary_filename = generate_timestamped_filename("red_team_summary")

    conversations_path = rogue_folder / conversations_filename
    summary_path = rogue_folder / summary_filename

    return conversations_path, summary_path


def ensure_directory_exists(file_path: Path) -> None:
    """
    Ensure the parent directory of a file path exists.

    Args:
        file_path: Path to file
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)


def save_to_file(content: str, file_path: Path) -> Path:
    """
    Save content to a file in the .rogue folder.

    Args:
        content: Content to save
        file_path: Path to save to

    Returns:
        Path to saved file
    """
    ensure_directory_exists(file_path)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Saved file to {file_path}")
    return file_path
