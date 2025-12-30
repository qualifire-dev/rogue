"""
Red Teaming Report Generation Module.

Generates compliance reports from red team results by mapping
vulnerability findings to various security frameworks.
"""

from .generator import ComplianceReportGenerator

__all__ = ["ComplianceReportGenerator"]
