"""
OWASP Framework Module.

Note: Framework definitions have been moved to the catalog module.
This module is kept for backward compatibility.

Use rogue.server.red_teaming.catalog.framework_mappings for framework data.
"""

# Backward compatibility - framework data is now in catalog
from ...catalog.framework_mappings import FRAMEWORK_CATALOG, get_framework

# Re-export for backward compatibility
OWASP_LLM = get_framework("owasp-llm")

__all__ = ["FRAMEWORK_CATALOG", "get_framework", "OWASP_LLM"]
