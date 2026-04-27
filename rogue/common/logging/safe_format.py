"""Patch loguru so f-string-evaluated messages don't crash on literal braces.

Loguru calls ``message.format(*args, **kwargs)`` on the log message whenever
any args/kwargs are passed to a level method (including ``extra={...}``).
Our codebase liberally uses the ``logger.X(f"... {val}", extra={...})`` shape
and ``val`` may carry user-controlled text — business context, runbook step
descriptions, LLM-generated chatter, JSON dicts. If ``val`` contains a
literal ``{name}`` substring, ``.format()`` interprets it as a placeholder
and crashes with ``KeyError`` (or ``IndexError`` for bare ``{}``).

Fix: escape ``{`` -> ``{{`` and ``}`` -> ``}}`` in the message string before
loguru sees it. Loguru's ``.format()`` then unescapes them back, so the
emitted message text is identical to the original; the crash window is just
closed. Extras still flow through loguru's normal mechanism (loguru
recognises ``extra=`` as a kwarg and merges it into ``record["extra"]``).

Patch is applied to ``loguru._logger.Logger`` directly (not the singleton)
so any clone returned by ``logger.bind()`` / ``logger.opt()`` also inherits
the safe behaviour.
"""

from loguru._logger import Logger

_LEVEL_METHODS = (
    "trace",
    "debug",
    "info",
    "success",
    "warning",
    "error",
    "critical",
    "exception",
)

_PATCHED_FLAG = "_rogue_safe_brace_format_patched"


def install() -> None:
    """Idempotently wrap each level method on the Logger class."""
    if getattr(Logger, _PATCHED_FLAG, False):
        return

    for level in _LEVEL_METHODS:
        original = getattr(Logger, level, None)
        if original is None:
            continue

        def make_wrapper(orig):
            def wrapper(self, __message, *args, **kwargs):
                if (args or kwargs) and isinstance(__message, str):
                    __message = __message.replace("{", "{{").replace("}", "}}")
                return orig(self, __message, *args, **kwargs)

            wrapper.__wrapped__ = orig
            return wrapper

        setattr(Logger, level, make_wrapper(original))

    setattr(Logger, _PATCHED_FLAG, True)
