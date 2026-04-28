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

# Tell litellm to silently drop provider-specific params it can't honour
# (e.g. `temperature` on the gpt-5 family, which only accepts the default
# of 1, or other model-specific kwargs other providers reject). Set once
# here at package import so every `from litellm import (a)completion`
# downstream inherits it — avoids per-call sprinkling and per-model branching.
# Wrapped in try/except because litellm is heavy and a few import paths
# (e.g. tooling that just touches `rogue.common.version`) shouldn't pay for
# importing it.
try:
    import litellm

    litellm.drop_params = True
except Exception:  # noqa: BLE001 - litellm is optional for some import paths
    pass

# Import submodules for backward compatibility
from . import (
    common,
    evaluator_agent,
    models,
    prompt_injection_evaluator,
    run_cli,
    run_server,
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
    "run_server",
    "get_version",
]


# Version info
__version__ = get_version("rogue-ai")
__author__ = "Rogue Security"
__description__ = "Library for evaluating AI agents against scenarios"
