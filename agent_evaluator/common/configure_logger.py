import sys

from loguru import logger


def configure_logger() -> None:
    logger.remove(None)
    logger.add(
        sink=sys.stdout,
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level> - {extra}",
        backtrace=True,
    )
