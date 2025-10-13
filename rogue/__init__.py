"""
Rogue Agent Evaluator - Core Library

This module provides a clean, library-oriented API for agent evaluation.
"""

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

# Version info
__version__ = "0.1.11"
__author__ = "Qualifire"
__description__ = "Library for evaluating AI agents against scenarios"
