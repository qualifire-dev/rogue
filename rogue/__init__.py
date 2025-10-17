"""
Rogue Agent Evaluator - Core Library

This module provides a clean, library-oriented API for agent evaluation.
"""

from pathlib import Path

# Import submodules for backward compatibility
from . import (
    common,
    evaluator_agent,
    models,
    prompt_injection_evaluator,
    run_cli,
    run_server,
    run_ui,
    ui,
)

# Import the new library interface
from .server.services.evaluation_library import EvaluationLibrary

# Main library interface
evaluate_agent = EvaluationLibrary.evaluate_agent
evaluate_agent_streaming = EvaluationLibrary.evaluate_agent_streaming
evaluate_agent_sync = EvaluationLibrary.evaluate_agent_sync

# Convenience exports
__all__ = [
    # Main evaluation functions
    "evaluate_agent",
    "evaluate_agent_streaming",
    "evaluate_agent_sync",
    # Core classes
    "EvaluationLibrary",
    # Submodules (backward compatibility)
    "common",
    "evaluator_agent",
    "models",
    "prompt_injection_evaluator",
    "run_cli",
    "run_ui",
    "run_server",
    "ui",
]

# Read version from VERSION file
def _get_version() -> str:
    try:
        # In development, prioritize VERSION file over installed metadata
        version_file = Path(__file__).parent.parent / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
    except Exception:
        pass
    
    try:
        # Fall back to installed package metadata
        from importlib.metadata import version
        return version("rogue-ai")
    except Exception:
        return "0.0.0-dev"

# Version info
__version__ = _get_version()
__author__ = "Qualifire"
__description__ = "Library for evaluating AI agents against scenarios"
