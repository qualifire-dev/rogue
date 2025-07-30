#!/usr/bin/env python3
"""
Phase 2 SDK Testing Script

Tests both TypeScript and Python SDKs structure and basic functionality.
"""

import sys
from pathlib import Path

# Add Python SDK to path
sys.path.insert(0, str(Path(__file__).parent / "sdks" / "python"))


def test_python_sdk_imports():
    """Test that Python SDK imports work correctly."""
    # Test imports
    from rogue_client import RogueSDK, RogueClientConfig, AuthType, ScenarioType
    from rogue_client.types import AgentConfig, Scenario, EvaluationRequest
    from rogue_client.client import RogueHttpClient
    from rogue_client.websocket import RogueWebSocketClient

    # Test instantiation
    config = RogueClientConfig(base_url="http://localhost:8000")
    RogueSDK(config)  # Test instantiation
    RogueHttpClient(config)  # Test instantiation
    RogueWebSocketClient("http://localhost:8000")  # Test instantiation

    # Test type definitions
    agent_config = AgentConfig(
        evaluated_agent_url="http://localhost:3000",
        evaluated_agent_auth_type=AuthType.NO_AUTH,
        judge_llm_model="openai/gpt-4o-mini",
    )
    scenario = Scenario(scenario="Test scenario", scenario_type=ScenarioType.POLICY)
    EvaluationRequest(
        agent_config=agent_config, scenarios=[scenario]
    )  # Test instantiation

    # If we get here, all imports and instantiations worked
    assert True  # nosec B101


def test_typescript_sdk_structure():
    """Test TypeScript SDK structure and files."""
    sdk_dir = Path(__file__).parent / "packages" / "sdk"

    required_files = [
        "package.json",
        "tsconfig.json",
        "src/index.ts",
        "src/types.ts",
        "src/client.ts",
        "src/websocket.ts",
        "src/sdk.ts",
        "README.md",
    ]

    # Check all required files exist
    for file_path in required_files:
        full_path = sdk_dir / file_path
        assert full_path.exists(), f"Missing file: {file_path}"  # nosec B101

    # Check package.json content
    import json

    package_json = json.loads((sdk_dir / "package.json").read_text())

    assert (
        package_json.get("name") == "@rogue/sdk"
    ), "Incorrect package name"  # nosec B101
    assert "typescript" in package_json.get(  # nosec B101
        "devDependencies", {}
    ), "TypeScript not in devDependencies"


def test_phase2_summary():
    """Test that Phase 2 deliverables are complete."""
    # This test verifies that both SDKs are properly structured
    # The actual functionality tests would require a running server

    # Check Python SDK structure
    python_sdk_dir = Path(__file__).parent / "sdks" / "python"
    assert python_sdk_dir.exists(), "Python SDK directory missing"  # nosec B101
    assert (
        python_sdk_dir / "rogue_client"
    ).exists(), "Python SDK package missing"  # nosec B101
    assert (
        python_sdk_dir / "README.md"
    ).exists(), "Python SDK README missing"  # nosec B101

    # Check TypeScript SDK structure
    ts_sdk_dir = Path(__file__).parent / "packages" / "sdk"
    assert ts_sdk_dir.exists(), "TypeScript SDK directory missing"  # nosec B101
    assert (
        ts_sdk_dir / "src"
    ).exists(), "TypeScript SDK src directory missing"  # nosec B101
    assert (
        ts_sdk_dir / "README.md"
    ).exists(), "TypeScript SDK README missing"  # nosec B101

    # If we get here, Phase 2 structure is complete
    assert True  # nosec B101


# This file can also be run as a script for manual testing
if __name__ == "__main__":
    print("🚀 Phase 2: SDK Testing")
    print("=" * 60)
    print("Run with: pytest test_phase2_sdks.py -v")
    print("For manual testing, use the individual test functions.")
