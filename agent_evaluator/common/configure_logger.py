import sys

from loguru import logger


def configure_logger(file_path: str | None = None) -> None:
    logger.remove(None)
    logger.add(
        sink=file_path or sys.stdout,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level> - {extra}",
        backtrace=True,
    )
