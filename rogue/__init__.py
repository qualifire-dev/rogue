"""
Rogue Agent Evaluator - Core Library

This module provides a clean, library-oriented API for agent evaluation.
"""

from datetime import datetime

# Import submodules for backward compatibility
t1 = datetime.now()
from . import common

t2 = datetime.now()
from . import evaluator_agent

t3 = datetime.now()
from . import models

t4 = datetime.now()
from . import prompt_injection_evaluator

t5 = datetime.now()
from . import run_cli

t6 = datetime.now()
from . import run_server

t7 = datetime.now()
from . import run_ui

t8 = datetime.now()
from . import ui

t9 = datetime.now()

# Import the new library interface
from .server.services.evaluation_library import EvaluationLibrary

t10 = datetime.now()

print(f"Common: {(t2 - t1).total_seconds()}")
print(f"Evaluator Agent: {(t3 - t2).total_seconds()}")
print(f"Models: {(t4 - t3).total_seconds()}")
print(f"Prompt Injection Evaluator: {(t5 - t4).total_seconds()}")
print(f"Run CLI: {(t6 - t5).total_seconds()}")
print(f"Run Server: {(t7 - t6).total_seconds()}")
print(f"Run UI: {(t8 - t7).total_seconds()}")
print(f"UI: {(t9 - t8).total_seconds()}")
print(f"Evaluation Library: {(t10 - t9).total_seconds()}")


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
__version__ = "0.1.7"
__author__ = "Qualifire"
__description__ = "Library for evaluating AI agents against scenarios"
