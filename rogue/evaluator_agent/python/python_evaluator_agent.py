"""
Python Evaluator Agent - Direct Python function-based agent evaluation.

This module provides an evaluator agent that calls a user-provided Python
function directly, without requiring network protocols like A2A or MCP.
"""

import asyncio
import sys
import importlib.util
from pathlib import Path
from types import ModuleType, TracebackType
from typing import Any, Callable, Optional, Self, Type

from loguru import logger
from rogue_sdk.types import Protocol, Scenarios

from ..base_evaluator_agent import BaseEvaluatorAgent


class PythonEvaluatorAgent(BaseEvaluatorAgent):
    """
    Evaluator agent that calls a Python function directly.

    The user provides a Python file path containing a `call_agent` function
    with the signature: `call_agent(messages: list[dict]) -> str`

    Where messages is a list of dicts with 'role' and 'content' keys,
    following the OpenAI messages format.
    """

    def __init__(
        self,
        python_file_path: str,
        judge_llm: str,
        scenarios: Scenarios,
        business_context: Optional[str],
        headers: Optional[dict[str, str]] = None,
        judge_llm_auth: Optional[str] = None,
        judge_llm_aws_access_key_id: Optional[str] = None,
        judge_llm_aws_secret_access_key: Optional[str] = None,
        judge_llm_aws_region: Optional[str] = None,
        debug: bool = False,
        deep_test_mode: bool = False,
        chat_update_callback: Optional[Callable[[dict], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            evaluated_agent_address=python_file_path,  # Store path as address
            protocol=Protocol.PYTHON,
            transport=None,  # No transport for Python protocol
            headers=headers,
            judge_llm=judge_llm,
            scenarios=scenarios,
            business_context=business_context,
            judge_llm_auth=judge_llm_auth,
            judge_llm_aws_access_key_id=judge_llm_aws_access_key_id,
            judge_llm_aws_secret_access_key=judge_llm_aws_secret_access_key,
            judge_llm_aws_region=judge_llm_aws_region,
            debug=debug,
            deep_test_mode=deep_test_mode,
            chat_update_callback=chat_update_callback,
            **kwargs,
        )
        self._python_file_path = Path(python_file_path)
        logger.debug(
            f"🐍 PythonEvaluatorAgent init - "
            f"python_file_path arg: {python_file_path!r}, "
            f"resolved: {self._python_file_path.absolute()}",
        )
        self._module: Optional[ModuleType] = None
        self._call_agent_fn: Optional[Callable[[list[dict[str, Any]]], str]] = None
        # Track if we added to sys.path so we can clean up
        self._added_sys_path: Optional[str] = None

    def _load_python_module(self) -> None:
        """Load the user's Python module and validate the call_agent function."""
        if not self._python_file_path.exists():
            raise FileNotFoundError(
                f"Python entrypoint file not found: {self._python_file_path}",
            )

        if not self._python_file_path.is_file():
            raise ValueError(
                f"Python entrypoint path is not a file: {self._python_file_path}",
            )

        # Prevent accidentally loading the evaluator's own file
        resolved_path = self._python_file_path.resolve()
        this_file = Path(__file__).resolve()
        if resolved_path == this_file:
            raise ValueError(
                "Cannot use the PythonEvaluatorAgent module as the entrypoint. "
                "Provide the path to YOUR agent's Python file with call_agent(). "
                "Example: examples/tshirt_store_langgraph_agent/"
                "python_entrypoint_shirtify.py",
            )

        logger.info(
            f"📦 Loading Python entrypoint module: {self._python_file_path}",
        )

        # Add the entrypoint file's directory to sys.path so imports work
        # This allows the entrypoint to import sibling modules
        import sys

        entrypoint_dir = str(self._python_file_path.parent.resolve())
        if entrypoint_dir not in sys.path:
            sys.path.insert(0, entrypoint_dir)
            self._added_sys_path = entrypoint_dir
            logger.debug(f"Added {entrypoint_dir} to sys.path for module imports")

        # Load the module dynamically
        module_name = self._python_file_path.stem
        spec = importlib.util.spec_from_file_location(
            module_name,
            self._python_file_path,
        )

        if spec is None or spec.loader is None:
            raise ImportError(
                f"Could not load module spec from: {self._python_file_path}",
            )

        self._module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self._module)

        # Validate call_agent function exists
        if not hasattr(self._module, "call_agent"):
            raise AttributeError(
                f"Python entrypoint module must have a 'call_agent' function: "
                f"{self._python_file_path}",
            )

        self._call_agent_fn = getattr(self._module, "call_agent")

        if not callable(self._call_agent_fn):
            raise TypeError(
                f"'call_agent' in {self._python_file_path} is not callable",
            )

        logger.info(
            f"✅ Successfully loaded call_agent function from {self._python_file_path}",
        )

    async def __aenter__(self) -> Self:
        """Load the Python module when entering the async context."""
        self._load_python_module()
        return await super().__aenter__()

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Clean up when exiting the async context."""
        await super().__aexit__(exc_type, exc_value, traceback)
        # Clean up sys.path if we added to it
        if self._added_sys_path:

            try:
                sys.path.remove(self._added_sys_path)
                logger.debug(f"Removed {self._added_sys_path} from sys.path")
            except ValueError:
                pass  # Already removed
            self._added_sys_path = None

    async def _send_message_to_evaluated_agent(
        self,
        context_id: str,
        message: str,
    ) -> dict[str, str]:
        """
        Sends a message to the evaluated agent by calling the Python function.

        :param message: the text to send to the agent.
        :param context_id: The context ID of the conversation.
            Each conversation has a unique context_id. All messages in the conversation
            have the same context_id.
        :return: A dictionary containing the response from the evaluated agent.
            - "response": the response string. If there is no response
                from the agent, the string is empty.
        """
        if self._call_agent_fn is None:
            raise RuntimeError(
                "Python module not loaded. Call __aenter__ first or use async with.",
            )

        try:
            logger.info(
                "🐍 Calling Python entrypoint function",
                extra={
                    "message": message[:100] + "..." if len(message) > 100 else message,
                    "context_id": context_id,
                    "python_file": str(self._python_file_path),
                },
            )

            # Add the user message to chat history
            self._add_message_to_chat_history(context_id, "user", message)

            # Build messages list from chat history (single source of truth)
            chat_history = self._context_id_to_chat_history.get(context_id)
            messages = (
                [
                    {"role": msg.role, "content": msg.content}
                    for msg in chat_history.messages
                ]
                if chat_history
                else [{"role": "user", "content": message}]
            )

            # Call the user's function
            response = await self._invoke_call_agent(messages)

            # Add the assistant response to chat history
            self._add_message_to_chat_history(context_id, "assistant", response)

            logger.info(
                "✅ Python entrypoint call successful",
                extra={
                    "response_length": len(response),
                    "response_preview": (
                        response[:100] + "..." if len(response) > 100 else response
                    ),
                    "context_id": context_id,
                },
            )

            return {"response": response}

        except Exception as e:
            logger.exception(
                "❌ Python entrypoint call failed",
                extra={
                    "message": message[:100] + "..." if len(message) > 100 else message,
                    "context_id": context_id,
                    "python_file": str(self._python_file_path),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return {"response": "", "error": str(e)}

    async def _invoke_call_agent(
        self,
        messages: list[dict[str, Any]],
    ) -> str:
        """
        Invoke the call_agent function, handling both sync and async versions.

        :param messages: List of message dicts with 'role' and 'content' keys.
        :return: The agent's response as a string.
        """
        if self._call_agent_fn is None:
            raise RuntimeError("call_agent function not loaded")

        result = self._call_agent_fn(messages)

        # Handle async functions
        if asyncio.iscoroutine(result):
            result = await result

        # Ensure result is a string
        if not isinstance(result, str):
            result = str(result)

        return result
