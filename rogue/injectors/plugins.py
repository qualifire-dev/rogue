"""
Custom injector plugin loading for Rogue Resilience.

Third-party and in-repo injectors can register via ``register_injector()``
or ship as a Python module exposing ``INJECTOR_CLASS``.

Example plugin module (``my_injector.py``)::

    from rogue.injectors.base_injector import BaseInjector, InjectorId, ...

    class MyInjector(BaseInjector):
        id = "my_custom_injector"  # string id for custom injectors
        name = "My Custom Injector"
        ...

        async def inject(self, target_agent_id, context):
            ...

        def get_probe_messages(self):
            return ["probe message"]

    INJECTOR_CLASS = MyInjector
"""

import importlib.util
from pathlib import Path
from typing import Callable, Type

from rogue.common.logging import get_logger

from .base_injector import BaseInjector
from .registry import InjectorDefinition, register_injector_definition

logger = get_logger(__name__)


def load_injector_plugin(path: str | Path) -> str:
    """
    Load an injector class from a Python file and register it.

    The module must define ``INJECTOR_CLASS`` pointing to a ``BaseInjector``
    subclass with ``id``, ``name``, and ``description`` class attributes.

    Args:
        path: Path to a ``.py`` plugin file.

    Returns:
        Registered injector ID string.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the module is invalid or missing ``INJECTOR_CLASS``.
        TypeError: If ``INJECTOR_CLASS`` is not a ``BaseInjector`` subclass.
    """
    plugin_path = Path(path).resolve()
    if not plugin_path.is_file():
        raise FileNotFoundError(f"Injector plugin not found: {plugin_path}")

    spec = importlib.util.spec_from_file_location(
        f"rogue_injector_plugin_{plugin_path.stem}",
        plugin_path,
    )
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load injector plugin: {plugin_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    injector_cls = getattr(module, "INJECTOR_CLASS", None)
    if injector_cls is None:
        raise ValueError(
            f"Plugin {plugin_path} must define INJECTOR_CLASS = <BaseInjector subclass>",
        )
    if not isinstance(injector_cls, type) or not issubclass(injector_cls, BaseInjector):
        raise TypeError("INJECTOR_CLASS must be a BaseInjector subclass")

    injector_id = getattr(injector_cls, "id", None)
    name = getattr(injector_cls, "name", injector_cls.__name__)
    description = getattr(injector_cls, "description", "")
    if not injector_id or not isinstance(injector_id, str):
        raise ValueError(f"Plugin {plugin_path} injector must set id: str")

    register_injector_definition(
        InjectorDefinition(
            id=injector_id,
            name=str(name),
            description=str(description),
            factory=injector_cls,
            premium=getattr(injector_cls, "premium", False),
            custom=True,
        ),
    )
    logger.info("Registered custom injector plugin", extra={"id": injector_id, "path": str(plugin_path)})
    return injector_id


def register_injector(
    injector_id: str,
    name: str,
    description: str,
    factory: Callable[[], BaseInjector],
    *,
    premium: bool = False,
) -> None:
    """
    Register a custom injector programmatically.

    Args:
        injector_id: Stable string identifier (not required to be ``InjectorId``).
        name: Display name for UI and reports.
        description: Short strategy summary.
        factory: Callable returning a fresh injector instance.
        premium: Whether this injector requires Rogue Security / Deckard.
    """
    register_injector_definition(
        InjectorDefinition(
            id=injector_id,
            name=name,
            description=description,
            factory=factory,
            premium=premium,
            custom=True,
        ),
    )
