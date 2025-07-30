"""
Logging configuration using loguru with structured logging support.

Provides centralized logging configuration with context variable support
and structured logging using the extra= pattern.
"""

import sys
import os
from typing import Dict, Any, Optional
from loguru import logger

from .context import get_all_context_vars


class LogConfig:
    """Logging configuration settings."""

    # Log levels
    STDOUT_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Format settings
    ENABLE_COLORS = os.getenv("LOG_COLORS", "true").lower() in ("true", "1", "yes")
    ENABLE_BACKTRACE = os.getenv("LOG_BACKTRACE", "true").lower() in (
        "true",
        "1",
        "yes",
    )

    # Development vs Production
    DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() in (
        "true",
        "1",
        "yes",
    )


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


def _format_extra_data(extra: Dict[str, Any]) -> str:
    """
    Format extra data for display in logs.

    Args:
        extra: Extra data dictionary

    Returns:
        Formatted string representation
    """
    if not extra:
        return ""

    # Handle nested extra structure
    if "extra" in extra and isinstance(extra["extra"], dict):
        extra_data = extra["extra"]
    else:
        extra_data = extra

    if not extra_data:
        return ""

    # Format as key=value pairs
    formatted_pairs = []
    for key, value in extra_data.items():
        if key in ["extra"]:  # Skip meta keys
            continue
        formatted_pairs.append(f"{key}={value}")

    return f"[{', '.join(formatted_pairs)}]" if formatted_pairs else ""


def configure_logger() -> None:
    """
    Configure loguru logger with structured logging support.

    Sets up:
    - Stdout sink with colored output
    - Context variable injection
    - Structured logging with extra data
    - Development vs production formatting
    """
    # Remove default logger
    logger.remove()

    # Determine format based on environment
    if LogConfig.DEVELOPMENT_MODE:
        # Development format - more readable
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        if LogConfig.ENABLE_COLORS:
            log_format += " <dim>{extra}</dim>"
        else:
            log_format += " {extra}"
    else:
        # Production format - more structured
        log_format = (
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message} {extra}"
        )

    # Add stdout sink
    logger.add(
        sink=sys.stdout,
        level=LogConfig.STDOUT_LOG_LEVEL,
        format=log_format,
        colorize=LogConfig.ENABLE_COLORS,
        backtrace=LogConfig.ENABLE_BACKTRACE,
        filter=_add_context_vars_filter,  # type: ignore[arg-type]
    )

    # Log configuration
    logger.info(
        "Logger configured",
        extra={
            "log_level": LogConfig.STDOUT_LOG_LEVEL,
            "development_mode": LogConfig.DEVELOPMENT_MODE,
            "colors_enabled": LogConfig.ENABLE_COLORS,
            "backtrace_enabled": LogConfig.ENABLE_BACKTRACE,
        },
    )


def get_logger(name: Optional[str] = None):
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
