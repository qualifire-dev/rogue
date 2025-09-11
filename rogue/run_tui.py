import shutil
import subprocess  # nosec: B404

from loguru import logger


def run_rogue_tui() -> int:
    """Run the rogue-tui binary."""
    logger.info("Running rogue-tui...")

    try:
        # Find the rogue-tui binary
        tui_path = shutil.which("rogue-tui")
        if not tui_path:
            logger.error("rogue-tui not found. Please install it first.")
            return 1

        # Run the rogue-tui with proper stdin/stdout handling
        result = subprocess.run([tui_path])  # nosec: B603
        return result.returncode

    except Exception:
        logger.exception("Error running rogue-tui")
        return 1
