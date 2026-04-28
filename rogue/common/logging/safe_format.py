"""Patch loguru so f-string-evaluated messages don't crash on literal braces.

Loguru calls ``message.format(*args, **kwargs)`` on the log message whenever
any args/kwargs are passed to a level method (including ``extra={...}``).
Our codebase pervasively uses the ``logger.X(f"... {val}", extra={...})``
shape and ``val`` may carry user-controlled text — business context,
runbook step descriptions, LLM-generated chatter, JSON dicts. If ``val``
contains a literal ``{name}`` substring, ``.format()`` interprets it as a
placeholder and crashes with ``KeyError`` (or ``IndexError`` for bare ``{}``).

Strategy: try the original level method first; if it raises ``KeyError`` or
``IndexError`` from the format substitution step, retry with the message's
braces escaped (``{`` → ``{{``, ``}`` → ``}}``). Loguru then unescapes them
back during ``.format()``, so the emitted log line is identical to the
original message text. This preserves loguru's documented format-style API
(``logger.info("user={user}", user=name)`` continues to work as before)
while making accidental braces in user content non-fatal.

The patch is applied to ``loguru._logger.Logger`` (the class, not the
singleton) so any clone returned by ``logger.bind()`` / ``logger.opt()``
inherits the safe behaviour. Idempotent.
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
    "log",
)

_PATCHED_FLAG = "_rogue_safe_brace_format_patched"


def _escape_braces(message: str) -> str:
    return message.replace("{", "{{").replace("}", "}}")


def install() -> None:
    """Idempotently wrap each level method on the Logger class."""
    if getattr(Logger, _PATCHED_FLAG, False):
        return

    for level in _LEVEL_METHODS:
        original = getattr(Logger, level, None)
        if original is None:
            continue

        # The generic Logger.log signature is (level, message, *args, **kwargs)
        # — message is positional arg index 1, not 0. All other level methods
        # have message at index 0.
        message_pos = 1 if level == "log" else 0

        def make_wrapper(orig, level_name, msg_idx):
            def wrapper(self, *args, **kwargs):
                try:
                    return orig(self, *args, **kwargs)
                except (KeyError, IndexError):
                    if msg_idx >= len(args) or not isinstance(args[msg_idx], str):
                        raise
                    new_args = list(args)
                    new_args[msg_idx] = _escape_braces(new_args[msg_idx])
                    return orig(self, *new_args, **kwargs)

            # Standard functools-style wrapper attributes; ty doesn't model
            # these as known attrs of plain functions, so set via setattr.
            setattr(wrapper, "__wrapped__", orig)
            wrapper.__name__ = level_name
            wrapper.__doc__ = orig.__doc__
            return wrapper

        setattr(Logger, level, make_wrapper(original, level, message_pos))

    setattr(Logger, _PATCHED_FLAG, True)
