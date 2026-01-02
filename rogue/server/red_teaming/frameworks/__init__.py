"""
Security Frameworks Module.

Note: Framework definitions have been moved to the catalog module.
Use rogue.server.red_teaming.catalog.framework_mappings for framework data.

This module is kept for backward compatibility.
"""

from ..catalog.framework_mappings import (
    FRAMEWORK_CATALOG,
    get_all_frameworks,
    get_framework,
)

__all__ = ["FRAMEWORK_CATALOG", "get_framework", "get_all_frameworks"]
