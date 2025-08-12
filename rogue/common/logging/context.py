"""
Logging context management for structured logging.

Provides context variables that are automatically included in log messages.
"""

import contextvars
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Context variables for structured logging
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="")
job_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("job_id", default="")
agent_url_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "agent_url", default=""
)
scenario_count_var: contextvars.ContextVar[int] = contextvars.ContextVar(
    "scenario_count", default=0
)


def get_all_context_vars() -> List[contextvars.ContextVar]:
    """Get all defined context variables."""
    return [
        request_id_var,
        user_id_var,
        job_id_var,
        agent_url_var,
        scenario_count_var,
    ]


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """
    Set request-level context variables.

    Args:
        request_id: Unique request identifier (auto-generated if None)
        user_id: User identifier
        **kwargs: Additional context variables

    Returns:
        The request_id that was set
    """
    if request_id is None:
        request_id = str(uuid4())

    request_id_var.set(request_id)

    if user_id:
        user_id_var.set(user_id)

    # Set any additional context variables
    for key, value in kwargs.items():
        if key == "job_id" and value:
            job_id_var.set(str(value))
        elif key == "agent_url" and value:
            agent_url_var.set(str(value))
        elif key == "scenario_count" and value:
            scenario_count_var.set(int(value))

    return request_id


def set_job_context(job_id: str, agent_url: Optional[str] = None) -> None:
    """
    Set job-level context variables.

    Args:
        job_id: Evaluation job identifier
        agent_url: URL of the agent being evaluated
    """
    job_id_var.set(job_id)
    if agent_url:
        agent_url_var.set(agent_url)


def set_scenario_context(scenario_count: int) -> None:
    """
    Set scenario-level context variables.

    Args:
        scenario_count: Number of scenarios being evaluated
    """
    scenario_count_var.set(scenario_count)


def get_current_context() -> Dict[str, Any]:
    """
    Get all current context variable values.

    Returns:
        Dictionary of context variable names and values
    """
    context = {}
    for var in get_all_context_vars():
        value = var.get()
        if value:  # Only include non-empty values
            context[var.name] = value
    return context


def clear_context() -> None:
    """Clear all context variables."""
    for var in get_all_context_vars():
        try:
            # Get the default value from the context var definition
            if var is request_id_var:
                var.set("")
            elif var is user_id_var:
                var.set("")
            elif var is job_id_var:
                var.set("")
            elif var is agent_url_var:
                var.set("")
            elif var is scenario_count_var:
                var.set(0)
        except LookupError:
            # Context var not set, ignore
            pass
