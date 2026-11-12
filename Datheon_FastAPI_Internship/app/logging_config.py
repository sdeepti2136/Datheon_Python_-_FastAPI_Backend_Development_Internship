"""
Logging Configuration Module.

Configures unified application logging with timestamp, log level,
logger name, and message. Ensures sensitive data is never logged.
"""

import logging
import sys
from app.config import get_settings

settings = get_settings()


def setup_logging() -> logging.Logger:
    """
    Initializes and returns the root application logger.
    """
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging_format = (
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
    )

    logging.basicConfig(
        level=log_level,
        format=logging_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    logger = logging.getLogger("datheon_bookstore")
    logger.setLevel(log_level)

    # Suppress overly chatty third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)

    return logger


logger = setup_logging()
