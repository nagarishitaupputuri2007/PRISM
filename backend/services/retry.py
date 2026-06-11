# backend/utils/retry.py
# PRISM 2.7 — Enterprise Retry & Resilience Layer

"""
Centralized retry system for PRISM.

Responsibilities:
- retry failed operations
- exponential backoff
- transient failure recovery
- retry logging
- resilience handling
- retry observability

This layer DOES NOT:
- perform AI logic
- parse responses
- execute routing

Those responsibilities belong to:
- utils/ai_client.py
- engines/
- routers/
"""

import time
from collections.abc import Callable
from typing import Any

from backend.core.logging import (
    get_logger
)

from backend.core.metrics import (
    increment_counter,
    record_duration
)


# =========================================================
# LOGGER
# =========================================================

LOGGER = get_logger(__name__)


# =========================================================
# RETRY CONFIGURATION
# =========================================================

MAX_RETRIES = 3

BASE_DELAY_SECONDS = 1

BACKOFF_MULTIPLIER = 2


# =========================================================
# RETRYABLE ERROR DETECTION
# =========================================================

def is_retryable_error(
    error: Exception
) -> bool:
    """
    Detect whether an exception
    should trigger retry logic.
    """

    error_message = str(
        error
    ).lower()

    retryable_keywords = [

        "429",
        "rate limit",
        "timeout",
        "connection",
        "temporarily unavailable",
        "internal server error",
        "502",
        "503",
        "504"
    ]

    return any(
        keyword in error_message
        for keyword in retryable_keywords
    )


# =========================================================
# EXPONENTIAL BACKOFF
# =========================================================

def calculate_backoff_delay(
    attempt: int
) -> float:
    """
    Calculate retry delay using
    exponential backoff.
    """

    return (
        BASE_DELAY_SECONDS
        * (
            BACKOFF_MULTIPLIER
            ** (attempt - 1)
        )
    )


# =========================================================
# RETRY EXECUTOR
# =========================================================

def execute_with_retry(
    operation: Callable[..., Any],
    *args: Any,
    **kwargs: Any
) -> Any:
    """
    Execute operation with retries.

    Features:
    - retry detection
    - exponential backoff
    - observability
    - structured logging
    """

    increment_counter(
        "retry_requests_total"
    )

    operation_start = (
        time.perf_counter()
    )

    last_error: Exception | None = None

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            LOGGER.info(
                f"Executing operation "
                f"(attempt {attempt}/{MAX_RETRIES})"
            )

            result = operation(
                *args,
                **kwargs
            )

            execution_duration = (
                time.perf_counter()
                - operation_start
            )

            record_duration(
                "retry_execution_duration_seconds",
                execution_duration
            )

            increment_counter(
                "retry_success_total"
            )

            return result

        except Exception as error:

            last_error = error

            retryable = (
                is_retryable_error(
                    error
                )
            )

            LOGGER.warning(
                f"Operation failed "
                f"(attempt {attempt}/{MAX_RETRIES}): "
                f"{error}"
            )

            increment_counter(
                "retry_attempts_total"
            )

            # =================================================
            # NON-RETRYABLE FAILURE
            # =================================================

            if not retryable:

                LOGGER.error(
                    "Non-retryable error detected"
                )

                increment_counter(
                    "retry_non_retryable_failures_total"
                )

                raise

            # =================================================
            # FINAL FAILURE
            # =================================================

            if attempt >= MAX_RETRIES:

                LOGGER.error(
                    "Maximum retry attempts reached"
                )

                increment_counter(
                    "retry_failures_total"
                )

                break

            # =================================================
            # BACKOFF DELAY
            # =================================================

            delay = calculate_backoff_delay(
                attempt
            )

            LOGGER.info(
                f"Retrying in "
                f"{delay:.2f}s"
            )

            increment_counter(
                "retry_backoff_events_total"
            )

            time.sleep(
                delay
            )

    # =====================================================
    # FINAL ERROR
    # =====================================================

    execution_duration = (
        time.perf_counter()
        - operation_start
    )

    record_duration(
        "retry_failed_execution_duration_seconds",
        execution_duration
    )

    raise last_error