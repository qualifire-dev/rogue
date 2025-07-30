"""
Rogue Agent Evaluator - Core Library

This module provides a clean, library-oriented API for agent evaluation.
"""

# Import submodules for backward compatibility
from . import common
from . import evaluator_agent
from . import models
from . import prompt_injection_evaluator
from . import run_cli
from . import run_ui
from . import ui

# Import the new library interface
from .services.evaluation_library import EvaluationLibrary, quick_evaluate
from .models.config import AgentConfig, AuthType
from .models.scenario import Scenario, Scenarios, ScenarioType
from .models.evaluation_result import (
    EvaluationResults,
    EvaluationResult,
    ConversationEvaluation,
)

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
    "quick_evaluate",
    # Core classes
    "EvaluationLibrary",
    "AgentConfig",
    "Scenario",
    "Scenarios",
    "EvaluationResults",
    "EvaluationResult",
    "ConversationEvaluation",
    # Enums
    "AuthType",
    "ScenarioType",
    # Submodules (backward compatibility)
    "common",
    "evaluator_agent",
    "models",
    "prompt_injection_evaluator",
    "run_cli",
    "run_ui",
    "ui",
]

# Version info
__version__ = "1.0.0"
__author__ = "Qualifire"
__description__ = "Library for evaluating AI agents against scenarios"
