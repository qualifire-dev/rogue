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
    # Loguru natively understands `{{` and `}}` as escapes for literal `{`
    # and `}`, so input "Use {{var}} carefully" surfaces as "Use {var}
    # carefully" in the rendered message — this is loguru's documented
    # format-style behavior and the patch does not interfere with it (it
    # only kicks in when format() actually raises). Crash-free is the
    # contract; verbatim preservation of doubled braces is not.
    val = "Use {{var}} carefully"
    _logger.info(f"context: {val}", extra={"k": "v"})
    assert any("Use {var} carefully" in line for line in captured_sink)


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


def test_loguru_format_style_api_still_works(captured_sink):
    """The patch must not break loguru's documented format-style API:
    ``logger.info("user={user}", user="alice")`` should continue to render
    as ``user=alice``. The try-format-first strategy preserves this — only
    on format failure does it fall back to brace-escaping.
    """
    _logger.info("user={user} action={action}", user="alice", action="login")
    assert any("user=alice action=login" in line for line in captured_sink)


def test_log_method_also_patched(captured_sink):
    """Generic Logger.log(level, message, ...) is also wrapped so the same
    KeyError is suppressed."""
    _logger.log("INFO", "context: Hello {customer_name}", extra={"k": "v"})
    assert any("Hello {customer_name}" in line for line in captured_sink)


def test_install_marks_class_as_patched():
    """Pin the install side-effect — if a future refactor accidentally drops
    the install() call from rogue.common.logging.config, this assertion
    catches it."""
    from loguru._logger import Logger

    from rogue.common.logging.safe_format import _PATCHED_FLAG

    assert getattr(Logger, _PATCHED_FLAG, False) is True
