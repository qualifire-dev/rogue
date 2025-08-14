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
from .models.config import AgentConfig, AuthType
from .models.evaluation_result import (
    ConversationEvaluation,
    EvaluationResult,
    EvaluationResults,
)
from .models.scenario import Scenario, Scenarios, ScenarioType

# Import the new library interface
from .server.services.evaluation_library import EvaluationLibrary, quick_evaluate

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
    "run_server",
    "ui",
]

# Version info
__version__ = "1.0.0"
__author__ = "Qualifire"
__description__ = "Library for evaluating AI agents against scenarios"
