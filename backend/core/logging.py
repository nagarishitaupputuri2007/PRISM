# backend/utils/logging_config.py
# PRISM 2.5 — Enterprise Logging Infrastructure

"""
Centralized logging infrastructure for PRISM.

Responsibilities:
- unified logger formatting
- reusable logger creation
- environment-safe logging
- duplicate handler prevention
- production-safe configuration

This layer DOES NOT:
- contain business logic
- execute workflows
- manage application state
"""

import logging
import os
import sys


# =========================================================
# ENVIRONMENT CONFIGURATION
# =========================================================

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
)

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
).upper()


# =========================================================
# LOG FORMAT
# =========================================================

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


# =========================================================
# FORMATTER
# =========================================================

FORMATTER = logging.Formatter(
    LOG_FORMAT
)


# =========================================================
# ROOT LOGGER CONFIGURATION
# =========================================================

ROOT_LOGGER = logging.getLogger()

if not ROOT_LOGGER.handlers:

    ROOT_LOGGER.setLevel(
        LOG_LEVEL
    )

    console_handler = (
        logging.StreamHandler(
            sys.stdout
        )
    )

    console_handler.setFormatter(
        FORMATTER
    )

    ROOT_LOGGER.addHandler(
        console_handler
    )


# =========================================================
# UVICORN LOGGER NORMALIZATION
# =========================================================

for logger_name in [

    "uvicorn",
    "uvicorn.error",
    "uvicorn.access"
]:

    uvicorn_logger = logging.getLogger(
        logger_name
    )

    uvicorn_logger.handlers = (
        ROOT_LOGGER.handlers
    )

    uvicorn_logger.setLevel(
        LOG_LEVEL
    )

    uvicorn_logger.propagate = False


# =========================================================
# LOGGER FACTORY
# =========================================================

def get_logger(
    name: str
) -> logging.Logger:
    """
    Return standardized logger instance.
    """

    logger = logging.getLogger(
        name
    )

    logger.setLevel(
        LOG_LEVEL
    )

    return logger