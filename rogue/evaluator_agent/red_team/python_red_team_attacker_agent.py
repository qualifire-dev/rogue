"""Python Red Team Attacker Agent - Attacks using direct Python function calls."""

import asyncio
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Optional

from loguru import logger
from rogue_sdk.types import AuthType, Protocol, Transport

from ...server.red_teaming.models import RedTeamConfig
from .base_red_team_attacker_agent import BaseRedTeamAttackerAgent


class PythonRedTeamAttackerAgent(BaseRedTeamAttackerAgent):
    """
    Red team attacker agent using direct Python function calls.

    The user provides a Python file path containing a `call_agent` function
    with the signature: `call_agent(messages: list[dict]) -> str`

    Where messages is a list of dicts with 'role' and 'content' keys,
    following the OpenAI messages format.
    """

    def __init__(
        self,
        evaluated_agent_address: Optional[str],  # Can be None for PYTHON protocol
        protocol: Protocol,
        transport: Optional[Transport],
        auth_type: AuthType,
        auth_credentials: Optional[str],
        red_team_config: RedTeamConfig,
        business_context: str,
        attacker_llm: str,
        attacker_llm_auth: Optional[str],
        attacker_llm_aws_access_key_id: Optional[str],
        attacker_llm_aws_secret_access_key: Optional[str],
        attacker_llm_aws_region: Optional[str],
        judge_llm: str,
        judge_llm_auth: Optional[str],
        judge_llm_aws_access_key_id: Optional[str],
        judge_llm_aws_secret_access_key: Optional[str],
        judge_llm_aws_region: Optional[str],
        qualifire_api_key: Optional[str],
        python_entrypoint_file: Optional[str] = None,
        **kwargs: object,
    ):
        # Use python_entrypoint_file if provided, otherwise fall back to address
        python_file_path = python_entrypoint_file or evaluated_agent_address
        if python_file_path is None:
            raise ValueError(
                "Either python_entrypoint_file or evaluated_agent_address must be "
                "provided for PythonRedTeamAttackerAgent",
            )
        super().__init__(
            evaluated_agent_address=python_file_path,
            protocol=protocol,
            transport=transport,
            auth_type=auth_type,
            auth_credentials=auth_credentials,
            red_team_config=red_team_config,
            business_context=business_context,
            attacker_llm=attacker_llm,
            attacker_llm_auth=attacker_llm_auth,
            attacker_llm_aws_access_key_id=attacker_llm_aws_access_key_id,
            attacker_llm_aws_secret_access_key=attacker_llm_aws_secret_access_key,
            attacker_llm_aws_region=attacker_llm_aws_region,
            judge_llm=judge_llm,
            judge_llm_auth=judge_llm_auth,
            judge_llm_aws_access_key_id=judge_llm_aws_access_key_id,
            judge_llm_aws_secret_access_key=judge_llm_aws_secret_access_key,
            judge_llm_aws_region=judge_llm_aws_region,
            qualifire_api_key=qualifire_api_key,
        )
        self._python_file_path = Path(python_file_path)
        self._module: Optional[ModuleType] = None
        self._call_agent_fn: Optional[Callable[[list[dict[str, Any]]], str]] = None
        # Track conversation history per session_id for message building
        self._session_histories: dict[str, list[dict[str, Any]]] = {}

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

        logger.info(
            "📦 Loading Python entrypoint module "
            f"for red team: {self._python_file_path}",
        )

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

    async def __aenter__(self):
        """Load the Python module when entering the async context."""
        await super().__aenter__()
        self._load_python_module()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        """Clean up when exiting the async context."""
        # Clear session histories
        self._session_histories.clear()
        await super().__aexit__(exc_type, exc_value, traceback)

    async def _send_message_to_evaluated_agent(
        self,
        message: str,
        session_id: Optional[str],
    ) -> str:
        """Send attack message by calling the Python function directly."""
        if self._call_agent_fn is None:
            raise RuntimeError(
                "Python module not loaded. Call __aenter__ first or use async with.",
            )

        try:
            context_id = session_id or "default"

            logger.debug(
                f"Sending Python call to {self._python_file_path}",
                extra={"context_id": context_id, "message_preview": message[:100]},
            )

            # Initialize session history if needed
            if context_id not in self._session_histories:
                self._session_histories[context_id] = []

            # Add user message to session history
            self._session_histories[context_id].append(
                {
                    "role": "user",
                    "content": message,
                },
            )

            # Call the user's function
            messages = self._session_histories[context_id]
            response = await self._invoke_call_agent(messages)

            # Add assistant response to session history
            self._session_histories[context_id].append(
                {
                    "role": "assistant",
                    "content": response,
                },
            )

            logger.debug(
                "Received response from Python agent",
                extra={
                    "response_length": len(response),
                    "response_preview": response[:100] if response else "",
                },
            )

            return response

        except Exception as e:
            logger.error(
                f"Failed to call Python agent: {e}",
                extra={"python_file": str(self._python_file_path)},
            )
            return f"Error: {str(e)}"

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
