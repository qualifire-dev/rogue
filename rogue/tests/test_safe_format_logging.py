"""Regression tests for the loguru safe-format patch.

Without the patch, ``logger.X(f"... {val}", extra={...})`` crashes with
``KeyError`` when ``val`` happens to contain a literal ``{name}`` substring
(e.g. business context with ``{customer}`` in it). The patch escapes braces
in the message string before loguru calls ``str.format()`` on it, restoring
them via the format step's own ``{{`` / ``}}`` unescape so the emitted log
text is unchanged.
"""

import pytest
from loguru import logger as _logger

# Triggers safe_format.install() as an import side effect.
import rogue.common.logging  # noqa: F401


@pytest.fixture
def captured_sink():
    """Capture loguru output for inspection."""
    captured: list[str] = []
    handler_id = _logger.add(
        captured.append,
        format="{level: <8} | {message} - {extra}",
        level="DEBUG",
    )
    yield captured
    _logger.remove(handler_id)


def test_curly_braced_value_with_extras_does_not_crash(captured_sink):
    val = "Hello {customer_name}"
    _logger.info(f"context: {val}", extra={"k": "v"})
    assert any("Hello {customer_name}" in line for line in captured_sink)


def test_double_braced_value_with_extras_does_not_crash(captured_sink):
    val = "Use {{var}} carefully"
    _logger.info(f"context: {val}", extra={"k": "v"})
    assert any("Use {{var}} carefully" in line for line in captured_sink)


def test_bare_braces_with_extras_does_not_crash(captured_sink):
    _logger.info("context: {}", extra={"k": "v"})
    assert any("context: {}" in line for line in captured_sink)


def test_business_context_repr_in_fstring(captured_sink):
    """The classic crash: object repr embedded via f-string includes
    ``business_context='Hello {customer}'`` and a sibling kwarg triggers
    format substitution."""

    class Job:
        def __repr__(self):
            return "Job(business_context='Hello {customer}')"

    j = Job()
    _logger.info(f"Job: {j}", extra={"job_id": "x"})
    assert any("Hello {customer}" in line for line in captured_sink)


def test_extras_still_propagate_into_record(captured_sink):
    _logger.info("plain", extra={"foo": "bar"})
    assert any("'foo': 'bar'" in line for line in captured_sink)


def test_no_extras_no_change(captured_sink):
    # Without args/kwargs, the message passes through unmodified — the patch
    # only escapes when format() would otherwise be triggered.
    _logger.info("Hello {name} — should be left alone")
    assert any("Hello {name}" in line for line in captured_sink)


def test_idempotent_install():
    """Re-running install() must not double-wrap the methods."""
    from rogue.common.logging.safe_format import install

    install()
    install()
    install()
    # Sanity: no crash, and a log call still works.
    captured: list[str] = []
    handler_id = _logger.add(captured.append, format="{message}", level="DEBUG")
    try:
        _logger.info("ping {x} {y}", extra={"k": "v"})
        assert any("ping {x} {y}" in line for line in captured)
    finally:
        _logger.remove(handler_id)


def test_bind_clones_inherit_safe_methods(captured_sink):
    """logger.bind() returns a new instance — patch is on the class so the
    clone is also safe."""
    bound = _logger.bind(component="test")
    bound.info("clone msg with {customer}", extra={"k": "v"})
    assert any("with {customer}" in line for line in captured_sink)
