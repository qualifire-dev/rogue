"""
Python protocol agent client for resilience experiments.

Loads a user-provided ``call_agent`` entrypoint and invokes it with the same
conventions as ``PythonEvaluatorAgent``, without pulling in the full evaluator.
"""

import asyncio
import importlib.util
import inspect
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Optional

from rogue.common.logging import get_logger

logger = get_logger(__name__)


class PythonAgentClient:
    """
    Lightweight wrapper around a Python ``call_agent`` entrypoint.

    Used by the resilience orchestrator for single-agent injection experiments
    via the PYTHON protocol. The client handles module loading, optional
    ``context_id`` forwarding, and async/sync ``call_agent`` implementations.

    Example:
        client = PythonAgentClient("my_agent.py")
        client.load()
        response = await client.call_agent(
            [{"role": "user", "content": "Hello"}],
            context_id="session-1",
        )
        client.unload()
    """

    def __init__(self, python_file_path: str) -> None:
        """
        Initialize the client for a Python entrypoint file.

        Args:
            python_file_path: Path to a ``.py`` file defining ``call_agent()``.
        """
        self._python_file_path = Path(python_file_path)
        self._module: Optional[ModuleType] = None
        self._call_agent_fn: Optional[Callable[..., str]] = None
        self._added_sys_path: Optional[str] = None

    def load(self) -> None:
        """
        Load and validate the Python entrypoint module.

        Raises:
            FileNotFoundError: If the entrypoint path does not exist.
            ValueError: If the path is not a ``.py`` file.
            ImportError: If the module cannot be loaded.
            AttributeError: If ``call_agent`` is not defined.
        """
        if not self._python_file_path.exists():
            raise FileNotFoundError(
                f"Python entrypoint file not found: {self._python_file_path}",
            )
        if self._python_file_path.suffix.lower() != ".py":
            raise ValueError(
                f"Python entrypoint must end in .py: {self._python_file_path}",
            )

        module_name = f"rogue_resilience_entrypoint_{self._python_file_path.stem}"
        spec = importlib.util.spec_from_file_location(
            module_name,
            self._python_file_path,
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {self._python_file_path}")

        module = importlib.util.module_from_spec(spec)
        parent_dir = str(self._python_file_path.parent.resolve())
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
            self._added_sys_path = parent_dir

        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            logger.exception(
                "Failed to execute Python entrypoint module",
                extra={"path": str(self._python_file_path)},
            )
            raise ImportError(
                f"Error loading entrypoint {self._python_file_path}: {exc}",
            ) from exc

        if not hasattr(module, "call_agent"):
            raise AttributeError(
                f"{self._python_file_path} must define a call_agent() function",
            )

        self._module = module
        self._call_agent_fn = getattr(module, "call_agent")
        logger.info(
            "Loaded Python entrypoint for resilience testing",
            extra={"path": str(self._python_file_path.resolve())},
        )

    def unload(self) -> None:
        """Release loaded module references and clean up ``sys.path``."""
        self._module = None
        self._call_agent_fn = None
        if self._added_sys_path and self._added_sys_path in sys.path:
            sys.path.remove(self._added_sys_path)
        self._added_sys_path = None

    async def call_agent(
        self,
        messages: list[dict[str, Any]],
        context_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Invoke the loaded ``call_agent`` function.

        Args:
            messages: OpenAI-style message list with ``role`` and ``content``.
            context_id: Optional session identifier forwarded when supported.
            **kwargs: Per-turn side-data forwarded when ``call_agent`` accepts
                ``**kwargs`` (e.g. injector ``attach_kwargs``).

        Returns:
            Agent response string (empty string if the function returns None).

        Raises:
            RuntimeError: If the entrypoint has not been loaded.
            Exception: Re-raises exceptions from the user's ``call_agent``.
        """
        if self._call_agent_fn is None:
            raise RuntimeError("Python entrypoint not loaded. Call load() first.")

        fn = self._call_agent_fn
        call_kwargs: dict[str, Any] = {}
        signature = inspect.signature(fn)
        params = signature.parameters

        if "context_id" in params:
            call_kwargs["context_id"] = context_id
        if kwargs and any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        ):
            call_kwargs.update(kwargs)
        elif kwargs:
            logger.debug(
                "Dropping injector kwargs; call_agent does not accept **kwargs",
                extra={"keys": list(kwargs.keys())},
            )

        try:
            if asyncio.iscoroutinefunction(fn):
                result = await fn(messages, **call_kwargs)
            else:
                result = await asyncio.to_thread(fn, messages, **call_kwargs)
        except Exception as exc:
            logger.error(
                "call_agent invocation failed",
                extra={
                    "path": str(self._python_file_path),
                    "context_id": context_id,
                    "error": str(exc),
                },
            )
            raise

        return str(result) if result is not None else ""
