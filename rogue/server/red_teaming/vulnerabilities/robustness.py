"""
Robustness vulnerability detection.

Tests for agents being hijacked or showing input overreliance.
"""

from enum import Enum
from typing import List, Optional

from .base_vulnerability import BaseVulnerability


class RobustnessType(Enum):
    """Types of robustness vulnerabilities."""

    HIJACKING = "hijacking"
    INPUT_OVERRELIANCE = "input_overreliance"


class Robustness(BaseVulnerability):
    """
    Robustness vulnerability.

    Detects when an agent:
    - Can be hijacked or manipulated
    - Over-relies on user input without validation
    """

    name = "Robustness"

    def __init__(
        self,
        types: Optional[List[str]] = None,
    ):
        """
        Initialize Robustness vulnerability detector.

        Args:
            types: List of vulnerability types to test for.
                   If None, tests all types.
        """
        if types is None:
            enum_types = list(RobustnessType)
        else:
            # Convert string values to enum types
            enum_types = [
                RobustnessType(t) if isinstance(t, str) else t
                for t in types
                if isinstance(t, str) and t in [e.value for e in RobustnessType]
            ]

        super().__init__(types=enum_types)  # type: ignore[arg-type]
