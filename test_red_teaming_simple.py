#!/usr/bin/env python3
"""
Simple manual test for red teaming foundation.

Tests modules directly without importing the full rogue package.
"""

import sys
from pathlib import Path

# Add to path
base_path = Path(__file__).parent
sys.path.insert(0, str(base_path))
sys.path.insert(0, str(base_path / "sdks" / "python"))

print("=" * 80)
print("Testing Rogue Red Teaming Foundation (Simple)")
print("=" * 80)

# Test 1: Attack classes
print("\n1. Testing Attack Classes...")
try:
    # Import as a package
    from rogue.server.red_teaming.attacks.single_turn import (
        ROT13,
        Base64,
        Leetspeak,
        PromptInjection,
    )

    pi = PromptInjection()
    result = pi.enhance("test")
    print(f"   ✅ PromptInjection works: {len(result)} chars")

    b64 = Base64()
    result = b64.enhance("test")
    print(f"   ✅ Base64 works: {result}")

    rot13 = ROT13()
    result = rot13.enhance("test")
    print(f"   ✅ ROT13 works: {result}")

    leet = Leetspeak()
    result = leet.enhance("test")
    print(f"   ✅ Leetspeak works: {result}")

except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 2: Vulnerabilities
print("\n2. Testing Vulnerabilities...")
try:
    from rogue.server.red_teaming.vulnerabilities import (
        ExcessiveAgency,
        PromptLeakage,
        Robustness,
    )

    pl = PromptLeakage(types=["instructions"])
    print(f"   ✅ PromptLeakage: {[t.value for t in pl.get_types()]}")

    ea = ExcessiveAgency(types=["permissions"])
    print(f"   ✅ ExcessiveAgency: {[t.value for t in ea.get_types()]}")

    rb = Robustness(types=["hijacking"])
    print(f"   ✅ Robustness: {[t.value for t in rb.get_types()]}")

except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 3: OWASP Framework
print("\n3. Testing OWASP Framework...")
try:
    from rogue.server.red_teaming.frameworks.owasp import OWASPTop10

    owasp = OWASPTop10()
    print(f"   ✅ OWASPTop10: {owasp.get_name()}")
    print(f"      Categories: {len(owasp.get_categories())}")
    for cat in owasp.get_categories():
        print(f"         - {cat.id}: {cat.name}")

except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 4: SDK Types
print("\n4. Testing SDK Types...")
try:
    import rogue_sdk.types as types

    print(f"   ✅ EvaluationMode: {types.EvaluationMode.RED_TEAM.value}")

    from pydantic import HttpUrl

    config = types.AgentConfig(
        evaluated_agent_url=HttpUrl("http://localhost:10001"),
        evaluation_mode=types.EvaluationMode.RED_TEAM,
        owasp_categories=["LLM_01"],
    )
    print(f"   ✅ AgentConfig: mode={config.evaluation_mode.value}")

    red_team_result = types.RedTeamingResult(
        owasp_category="LLM_01",
        vulnerability_type="test",
        attack_method="test",
        severity="high",
        conversation_id="test",
    )
    print(f"   ✅ RedTeamingResult: {red_team_result.owasp_category}")

except Exception as e:
    print(f"   ❌ Failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ All Tests Passed!")
print("=" * 80)
