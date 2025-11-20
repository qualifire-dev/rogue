"""
Excessive agency vulnerability detection.

Tests for agents performing unauthorized actions or having too much autonomy.
"""

from enum import Enum
from typing import List, Optional

from .base_vulnerability import BaseVulnerability


class ExcessiveAgencyType(Enum):
    """Types of excessive agency vulnerabilities."""

    FUNCTIONALITY = "functionality"
    PERMISSIONS = "permissions"
    AUTONOMY = "autonomy"


class ExcessiveAgency(BaseVulnerability):
    """
    Excessive agency vulnerability.

    Detects when an agent:
    - Performs unauthorized functionality
    - Bypasses permission checks
    - Acts with excessive autonomy
    """

    name = "Excessive Agency"

    def __init__(
        self,
        types: Optional[List[str]] = None,
    ):
        """
        Initialize Excessive Agency vulnerability detector.

        Args:
            types: List of vulnerability types to test for.
                   If None, tests all types.
        """
        if types is None:
            enum_types = list(ExcessiveAgencyType)
        else:
            # Convert string values to enum types
            enum_types = [
                ExcessiveAgencyType(t) if isinstance(t, str) else t
                for t in types
                if isinstance(t, str) and t in [e.value for e in ExcessiveAgencyType]
            ]

        super().__init__(types=enum_types)  # type: ignore[arg-type]
