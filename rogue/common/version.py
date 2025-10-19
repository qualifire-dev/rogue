"""
Shared version retrieval logic.
"""
from pathlib import Path


def get_version(package_name: str) -> str:
    """
    Retrieves the package version.

    It first tries to find a 'VERSION' file by traversing up from the current
    file's location. If found, its content is returned.

    As a fallback, it tries to get the version from the installed package
    metadata using importlib.metadata.

    If both methods fail, it returns a default development version string.

    Args:
        package_name: The name of the package to look up in the metadata.

    Returns:
        The version string.
    """
    try:
        # Find project root by looking for the VERSION file
        current_path = Path(__file__).resolve()
        for parent in current_path.parents:
            version_file = parent / "VERSION"
            if version_file.exists():
                return version_file.read_text().strip()
    except Exception:
        pass  # nosec B110

    try:
        # Fall back to installed package metadata
        from importlib.metadata import version

        return version(package_name)
    except Exception:
        return "0.0.0-dev"