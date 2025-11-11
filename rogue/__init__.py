"""
Rogue Agent Evaluator - Core Library

This module provides a clean, library-oriented API for agent evaluation.
"""

import warnings

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="websockets.legacy is deprecated",
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="websockets.server.WebSocketServerProtocol is deprecated",
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="remove second argument of ws_handler",
)

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
from .common.version import get_version
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
    "get_version",
]


# Version info
__version__ = get_version("rogue-ai")
__author__ = "Qualifire"
__description__ = "Library for evaluating AI agents against scenarios"
