"""
Simple Deckard Client for Premium Attack Generation.

This module provides a simplified client interface for the Deckard premium attack
generation service. All premium attacks (single-turn, multi-turn, and agentic)
are routed through a single unified endpoint.

Premium attacks include:
- Single-turn: homoglyph, citation, gcg, likert, best-of-n
- Multi-turn: crescendo, goat, simba, mischievous-user
- Agentic: hydra, tree-jailbreak, meta-agent, iterative
"""

import os
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger


class DeckardClientError(Exception):
    """Error raised by DeckardClient."""

    pass


# Backwards compatibility alias
QualifireAttackClientError = DeckardClientError


class DeckardClient:
    """
    Simple client for Deckard premium attack service.

    This client provides a single entry point for all premium attack generation.
    The Deckard service handles routing to the appropriate attack type internally.

    Premium attacks include:
    - Single-turn premium: homoglyph, citation, gcg, likert, best-of-n
    - Multi-turn: crescendo, goat, simba, mischievous-user, linear, sequential
    - Agentic: hydra, tree-jailbreak, meta-agent, iterative
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize the Deckard client.

        Args:
            api_key: Qualifire API key for premium features
            base_url: Base URL for Deckard API (defaults to DECKARD_BASE_URL env var
                      or https://app.qualifire.ai)
        """
        self.api_key = api_key or os.getenv("QUALIFIRE_API_KEY")
        self.base_url = (
            base_url or os.getenv("DECKARD_BASE_URL") or "https://app.qualifire.ai"
        )
        self._is_configured = self.api_key is not None and len(self.api_key) > 0

        if self._is_configured:
            logger.info(
                "DeckardClient initialized with API key",
                extra={"base_url": self.base_url},
            )
        else:
            logger.debug("DeckardClient initialized without API key")

    @property
    def is_configured(self) -> bool:
        """Check if the client has a valid API key configured."""
        return self._is_configured

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "rogue-red-teaming/1.0",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def generate_attack_payload(
        self,
        attack_id: str,
        vulnerability_id: str,
        business_context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        attack_state: Optional[Dict[str, Any]] = None,
        turn_number: int = 1,
        attempt_num: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate an attack payload from Deckard service.

        This is the single entry point for ALL premium attacks. The Deckard
        service handles attack type routing internally based on attack_id.

        Args:
            attack_id: ID of the attack technique (e.g., 'homoglyph', 'goat', 'hydra')
            vulnerability_id: ID of the vulnerability to target
            business_context: Description of the target agent and its domain
            conversation_history: Previous messages (for multi-turn/agentic attacks)
            attack_state: Client-managed state (for agentic attacks)
            turn_number: Current turn number (for multi-turn attacks)
            attempt_num: Attempt number for generating variations (single-turn)

        Returns:
            Dictionary containing:
                - attack_message: The generated attack message
                - should_continue: Whether to continue (multi-turn/agentic)
                - updated_state: Updated state for next turn (agentic)
                - metadata: Additional attack metadata

        Raises:
            DeckardClientError: If API key is not configured or API call fails

        Example:
            >>> client = DeckardClient(api_key="...")
            >>> result = await client.generate_attack_payload(
            ...     attack_id="homoglyph",
            ...     vulnerability_id="bias-gender",
            ...     business_context="T-shirt store AI assistant"
            ... )
            >>> print(result["attack_message"])
        """
        if not self._is_configured:
            raise DeckardClientError(
                "QUALIFIRE_API_KEY required for premium attacks. "
                "Get your API key at https://qualifire.ai/api-keys",
            )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/attacks/generate",
                    headers=self._get_headers(),
                    json={
                        "attack_id": attack_id,
                        "vulnerability_id": vulnerability_id,
                        "business_context": business_context,
                        "conversation_history": conversation_history or [],
                        "attack_state": attack_state or {},
                        "turn_number": turn_number,
                        "attempt_num": attempt_num,
                    },
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Deckard API error: {e.response.status_code}",
                extra={"detail": e.response.text},
            )
            raise DeckardClientError(
                f"Attack generation failed: {e.response.status_code}",
            ) from e
        except Exception as e:
            logger.error(f"Deckard API call failed: {e}")
            raise DeckardClientError(f"Attack generation failed: {e}") from e

    async def list_attacks(self) -> Dict[str, Any]:
        """
        List available premium attack techniques.

        Returns:
            Dictionary with attacks list and total count
        """
        if not self._is_configured:
            return {"attacks": [], "total": 0}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/attacks",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to list attacks: {e}")
            return {"attacks": [], "total": 0}

    async def list_datasets(self) -> Dict[str, Any]:
        """
        List available premium datasets.

        Returns:
            Dictionary with datasets list and total count
        """
        if not self._is_configured:
            return {"datasets": [], "total": 0}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/datasets",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to list datasets: {e}")
            return {"datasets": [], "total": 0}

    def get_premium_attacks(self) -> List[str]:
        """
        Get list of premium attack IDs available with current API key.

        Returns:
            List of premium attack IDs
        """
        if not self._is_configured:
            return []

        return [
            # Single-turn premium
            "html-indirect-prompt-injection",
            "homoglyph",
            "citation",
            "gcg",
            "likert-jailbreak",
            "best-of-n",
            # Multi-turn
            "multi-turn-jailbreak",
            "goat",
            "mischievous-user",
            "simba",
            "crescendo",
            "linear-jailbreak",
            "sequential-jailbreak",
            "bad-likert-judge",
            # Agentic
            "iterative-jailbreak",
            "meta-agent-jailbreak",
            "hydra",
            "tree-jailbreak",
            "single-turn-composite",
        ]


# Backwards compatibility alias
QualifireAttackClient = DeckardClient
