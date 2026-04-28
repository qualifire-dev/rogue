import logging

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get the loguru-equivalent level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find the caller to get the correct stack depth. ``f_back`` is
        # Optional[FrameType] in the type stubs, so we narrow defensively —
        # in practice currentframe() always exists and the loop only walks
        # frames whose parent is ``logging.__file__`` (so f_back is never
        # really None in this scope).
        frame, depth = logging.currentframe(), 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            if frame.f_back is None:
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )
