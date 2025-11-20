"""
Base red teaming metric class.

Metrics evaluate whether a vulnerability was successfully exploited in a test case.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseRedTeamingMetric(ABC):
    """
    Base class for red teaming evaluation metrics.

    Metrics determine if a vulnerability was successfully exploited based on
    the agent's response to an attack.
    """

    score: Optional[float] = None
    reason: Optional[str] = None

    @abstractmethod
    def measure(self, test_case: Any) -> None:
        """
        Measure whether the vulnerability was exploited.

        Args:
            test_case: Test case containing attack input and agent response
        """
        raise NotImplementedError("Subclasses must implement measure()")

    async def a_measure(self, test_case: Any) -> None:
        """
        Async version of measure.

        Args:
            test_case: Test case containing attack input and agent response
        """
        return self.measure(test_case)
