"""Tests for custom injector plugin loading."""

from pathlib import Path

import pytest

from rogue.injectors import registry
from rogue.injectors.base_injector import BaseInjector, InjectionContext, InjectionResult
from rogue.injectors.plugins import load_injector_plugin, register_injector
from rogue.injectors.registry import get_injector, list_injectors

PLUGIN = (
    Path(__file__).parent.parent.parent
    / "examples"
    / "custom_injector_plugin"
    / "example_injector.py"
)


@pytest.fixture(autouse=True)
def _isolate_injector_registry() -> None:
    """Restore injector catalog state so plugin tests do not leak registrations."""
    catalog_snapshot = dict(registry.INJECTOR_CATALOG)
    custom_snapshot = dict(registry._CUSTOM_CATALOG)
    yield
    registry.INJECTOR_CATALOG.clear()
    registry.INJECTOR_CATALOG.update(catalog_snapshot)
    registry._CUSTOM_CATALOG.clear()
    registry._CUSTOM_CATALOG.update(custom_snapshot)


def test_load_injector_plugin_from_file() -> None:
    injector_id = load_injector_plugin(PLUGIN)
    assert injector_id == "echo_loop"
    injector = get_injector("echo_loop")
    assert injector.name == "Echo Loop"


def test_register_injector_programmatically() -> None:
    class TempInjector(BaseInjector):
        id = "temp_test_injector"
        name = "Temp"
        description = "temp"

        async def inject(self, target_agent_id: str, context: InjectionContext) -> InjectionResult:
            self._armed = True
            return InjectionResult(injector_id=self.id, target_agent_id=target_agent_id)

        def get_probe_messages(self) -> list[str]:
            return ["probe"]

    register_injector("temp_test_injector", "Temp", "temp", TempInjector)
    assert any(
        str(d.id) == "temp_test_injector" or getattr(d.id, "value", None) == "temp_test_injector"
        for d in list_injectors()
    )


@pytest.mark.asyncio
async def test_custom_plugin_produces_probes() -> None:
    load_injector_plugin(PLUGIN)
    injector = get_injector("echo_loop")
    result = await injector.inject("default", InjectionContext())
    assert len(result.probe_messages) >= 1


def test_load_injector_plugin_raises_value_error_on_syntax_error(tmp_path: Path) -> None:
    bad_plugin = tmp_path / "bad_plugin.py"
    bad_plugin.write_text("def broken(\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Cannot load injector plugin"):
        load_injector_plugin(bad_plugin)
