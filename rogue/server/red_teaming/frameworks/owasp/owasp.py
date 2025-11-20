"""
OWASP Top 10 for LLMs framework implementation.

Provides structured red teaming based on OWASP Top 10 for LLM Applications.
"""

from dataclasses import dataclass
from typing import List, Literal

from .risk_categories import OWASP_CATEGORIES, OWASPCategory


@dataclass
class OWASPTop10:
    """
    OWASP Top 10 for LLMs framework.

    Provides structured vulnerability testing based on OWASP categories.
    """

    name: str = "OWASP Top 10 for LLMs"
    description: str = "The OWASP Top 10 for LLM Applications 2025"

    ALLOWED_CATEGORIES = [
        "LLM_01",
        "LLM_02",
        "LLM_03",
        "LLM_04",
        "LLM_05",
        "LLM_06",
        "LLM_07",
        "LLM_08",
        "LLM_09",
        "LLM_10",
    ]

    def __init__(
        self,
        categories: List[
            Literal[
                "LLM_01",
                "LLM_02",
                "LLM_03",
                "LLM_04",
                "LLM_05",
                "LLM_06",
                "LLM_07",
                "LLM_08",
                "LLM_09",
                "LLM_10",
            ]
        ] = None,  # type: ignore[assignment]
    ):
        """
        Initialize OWASP Top 10 framework.

        Args:
            categories: List of OWASP category IDs to test.
                       If None, defaults to agent-relevant categories
                       (LLM_01, LLM_06, LLM_07)
        """
        if categories is None:
            # Default to agent-relevant categories
            categories = ["LLM_01", "LLM_06", "LLM_07"]

        self.categories = categories
        self.risk_categories: List[OWASPCategory] = []

        # Filter categories to only include those that are implemented
        for category_id in categories:
            for risk_category in OWASP_CATEGORIES:
                if risk_category.id == category_id:
                    self.risk_categories.append(risk_category)
                    break

    def get_name(self) -> str:
        """Get the framework name."""
        return self.name

    def get_categories(self) -> List[OWASPCategory]:
        """Get the selected risk categories."""
        return self.risk_categories
