# backend/utils/metrics.py
# PRISM 2.5 — Enterprise Observability Layer

"""
Centralized metrics system for PRISM.

Responsibilities:
- request metrics
- AI observability
- retry tracking
- cache analytics
- pipeline timing
- runtime diagnostics
- performance aggregation
- pipeline success tracking
- pipeline failure tracking

This layer DOES NOT:
- execute business logic
- perform AI reasoning
- handle routing

Those responsibilities belong to:
- routers/
- engines/
- ai_client/
"""

import time
from collections import defaultdict
from threading import Lock
from typing import Any

from backend.core.logging import (
    get_logger
)


# =========================================================
# LOGGER
# =========================================================

LOGGER = get_logger(__name__)


# =========================================================
# GLOBAL METRICS STATE
# =========================================================

COUNTERS = defaultdict(int)

DURATIONS = defaultdict(list)

METRICS_LOCK = Lock()

START_TIME = time.time()


# =========================================================
# COUNTER METRICS
# =========================================================

def increment_counter(
    metric_name: str,
    amount: int = 1
) -> None:
    """
    Increment numeric metric safely.
    """

    with METRICS_LOCK:

        COUNTERS[
            metric_name
        ] += amount


# =========================================================
# DURATION METRICS
# =========================================================

def record_duration(
    metric_name: str,
    duration: float
) -> None:
    """
    Record duration metric safely.
    """

    with METRICS_LOCK:

        DURATIONS[
            metric_name
        ].append(duration)


# =========================================================
# BACKWARD COMPATIBILITY ALIAS
# =========================================================

def add_duration(
    metric_name: str,
    duration: float
) -> None:
    """
    Alias maintained for performance.py compatibility.
    """

    record_duration(
        metric_name,
        duration
    )


# =========================================================
# PIPELINE SUCCESS TRACKING
# =========================================================

def track_pipeline_success(
    duration_seconds: float
) -> None:
    """
    Track successful pipeline execution.
    """

    increment_counter(
        "successful_pipelines"
    )

    record_duration(
        "pipeline_duration",
        duration_seconds
    )

    LOGGER.info(
        f"[Metrics] "
        f"Pipeline succeeded "
        f"({duration_seconds:.2f}s)"
    )


# =========================================================
# PIPELINE FAILURE TRACKING
# =========================================================

def track_pipeline_failure() -> None:
    """
    Track failed pipeline execution.
    """

    increment_counter(
        "failed_pipelines"
    )

    LOGGER.warning(
        "[Metrics] Pipeline failed"
    )


# =========================================================
# CACHE HIT TRACKING
# =========================================================

def track_cache_hit() -> None:
    """
    Track cache hit.
    """

    increment_counter(
        "cache_hits"
    )


# =========================================================
# CACHE MISS TRACKING
# =========================================================

def track_cache_miss() -> None:
    """
    Track cache miss.
    """

    increment_counter(
        "cache_misses"
    )


# =========================================================
# REQUEST TRACKING
# =========================================================

def track_request() -> None:
    """
    Track incoming request.
    """

    increment_counter(
        "requests"
    )


# =========================================================
# AVERAGE CALCULATION
# =========================================================

def calculate_average(
    values: list[float]
) -> float:

    if not values:

        return 0.0

    return round(
        sum(values) / len(values),
        2
    )


# =========================================================
# MAX CALCULATION
# =========================================================

def calculate_max(
    values: list[float]
) -> float:

    if not values:

        return 0.0

    return round(
        max(values),
        2
    )


# =========================================================
# MIN CALCULATION
# =========================================================

def calculate_min(
    values: list[float]
) -> float:

    if not values:

        return 0.0

    return round(
        min(values),
        2
    )


# =========================================================
# METRICS SNAPSHOT
# =========================================================

def get_metrics() -> dict[str, Any]:
    """
    Return metrics snapshot.
    """

    with METRICS_LOCK:

        counters_snapshot = dict(
            COUNTERS
        )

        durations_snapshot = {

            key: values.copy()

            for key, values in DURATIONS.items()
        }

    uptime_seconds = round(
        time.time() - START_TIME,
        2
    )

    duration_metrics = {}

    for metric_name, values in (
        durations_snapshot.items()
    ):

        duration_metrics[
            metric_name
        ] = {

            "count": len(values),

            "average_seconds":
                calculate_average(values),

            "max_seconds":
                calculate_max(values),

            "min_seconds":
                calculate_min(values)
        }

    return {

        "uptime_seconds":
            uptime_seconds,

        "counters":
            counters_snapshot,

        "durations":
            duration_metrics
    }


# =========================================================
# METRICS RESET
# =========================================================

def reset_metrics() -> None:
    """
    Reset metrics safely.
    """

    global START_TIME

    with METRICS_LOCK:

        COUNTERS.clear()

        DURATIONS.clear()

        START_TIME = time.time()

    LOGGER.warning(
        "All metrics reset"
    )