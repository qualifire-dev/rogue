"""
Utility for SDK path setup to avoid flake8 E402 errors
"""

import sys
from pathlib import Path


def setup_sdk_path() -> None:
    """Add the Python SDK to sys.path if not already present."""
    sdk_path = Path(__file__).parent.parent.parent / "sdks" / "python"
    if str(sdk_path) not in sys.path:
        sys.path.insert(0, str(sdk_path))


# Call it immediately when this module is imported
setup_sdk_path()
