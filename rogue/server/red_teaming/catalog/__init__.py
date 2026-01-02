"""
Red Teaming Catalog Module.

Provides catalogs of vulnerabilities, attacks, and framework mappings
for the vulnerability-centric red teaming system.
"""

from .attacks import ATTACK_CATALOG, get_attack, get_attacks_by_category
from .framework_mappings import FRAMEWORK_CATALOG, get_all_frameworks, get_framework
from .vulnerabilities import (
    VULNERABILITY_CATALOG,
    get_vulnerabilities_by_category,
    get_vulnerability,
)

__all__ = [
    # Vulnerabilities
    "VULNERABILITY_CATALOG",
    "get_vulnerability",
    "get_vulnerabilities_by_category",
    # Attacks
    "ATTACK_CATALOG",
    "get_attack",
    "get_attacks_by_category",
    # Frameworks
    "FRAMEWORK_CATALOG",
    "get_framework",
    "get_all_frameworks",
]
