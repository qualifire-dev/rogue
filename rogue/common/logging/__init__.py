"""
Structured logging system for Rogue Agent Evaluator.

Provides loguru-based logging with context variables and structured data support.

Usage:
    from rogue.common.logging import configure_logger, get_logger, set_request_context

    # Configure logging (do this once at startup)
    configure_logger()

    # Get a logger
    logger = get_logger(__name__)

    # Set context for structured logging
    set_request_context(request_id="req-123", user_id="user-456")

    # Log with extra data
    logger.info("Processing request", extra={
        "endpoint": "/api/v1/evaluations",
        "method": "POST",
        "duration_ms": 150
    })
"""

from .config import configure_logger, get_logger, LogConfig
from .context import (
    set_request_context,
    set_job_context,
    set_scenario_context,
    get_current_context,
    clear_context,
    request_id_var,
    user_id_var,
    job_id_var,
    agent_url_var,
    scenario_count_var,
)

__all__ = [
    # Configuration
    "configure_logger",
    "get_logger",
    "LogConfig",
    # Context management
    "set_request_context",
    "set_job_context",
    "set_scenario_context",
    "get_current_context",
    "clear_context",
    # Context variables
    "request_id_var",
    "user_id_var",
    "job_id_var",
    "agent_url_var",
    "scenario_count_var",
]
