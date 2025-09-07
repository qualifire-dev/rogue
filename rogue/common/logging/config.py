"""
Logging configuration using loguru with structured logging support.

Provides centralized logging configuration with context variable support
and structured logging using the extra= pattern.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger

from .context import get_all_context_vars
from .intercept_handler import InterceptHandler


def _add_context_vars_filter(record: Dict[str, Any]) -> bool:
    """
    Filter to add context variables to log records.

    This filter adds all context variables to the log record's extra data,
    supporting the logger.info(msg, extra={"key": "value"}) pattern.
    """
    for context_var in get_all_context_vars():
        value = context_var.get()
        if value is None or (isinstance(value, (str, int)) and not value):
            continue

        # Handle nested extra dict structure
        # When using logger.info(msg, extra={"my_var": my_var}),
        # loguru creates record["extra"]["extra"]["my_var"]
        record_extra = record["extra"]
        inner_extra = record_extra.get("extra", {})

        # Add context variable to inner extra dict
        inner_extra[context_var.name] = value

        # Ensure the nested structure exists
        if "extra" not in record_extra:
            record_extra["extra"] = inner_extra

    return True


def intercept_uvicorn_logging() -> None:
    # Disable Uvicorn's default loggers
    loggers = (
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
    )
    uvicorn_handler = InterceptHandler()
    for logger_name in loggers:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [uvicorn_handler]


def configure_logger(
    debug: bool = False,
    file_path: Path | str | None = None,
) -> None:
    logger.remove(None)

    if file_path:
        logger.add(
            sink=file_path,
            level="DEBUG" if debug else "INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message} - {extra}",
            backtrace=True,
            rotation="10 MB",
            colorize=False,
            filter=_add_context_vars_filter,  # type: ignore[arg-type]
        )
    else:
        logger.add(
            sink=sys.stdout,
            level="DEBUG" if debug else "INFO",
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level> - {extra}",
            backtrace=True,
            colorize=True,
            filter=_add_context_vars_filter,  # type: ignore[arg-type]
        )
    intercept_uvicorn_logging()


def get_logger(name: str | None = None):
    """
    Get a logger instance.

    Args:
        name: Logger name (defaults to caller's module)

    Returns:
        Configured logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger
