# backend/utils/cache.py
# PRISM 2.4 — Enterprise TTL Cache Layer

"""
Centralized caching system for PRISM.

Responsibilities:
- cache storage
- TTL expiration
- cache invalidation
- cache observability
- thread safety
- memory-safe eviction
- runtime diagnostics

This layer DOES NOT:
- perform AI logic
- execute business rules
- handle routing

Those responsibilities belong to:
- engines/
- routers/
"""

import time
from dataclasses import dataclass
from threading import Lock
from typing import Any

from backend.core.logging import (
    get_logger
)

from backend.core.metrics import (
    increment_counter
)


# =========================================================
# LOGGER
# =========================================================

LOGGER = get_logger(__name__)


# =========================================================
# CACHE ENTRY MODEL
# =========================================================

@dataclass
class CacheEntry:

    value: Any

    created_at: float

    expires_at: float


# =========================================================
# CACHE CONFIGURATION
# =========================================================

DEFAULT_TTL_SECONDS = 60 * 60

MAX_CACHE_SIZE = 100


# =========================================================
# CACHE STATE
# =========================================================

CACHE: dict[
    str,
    CacheEntry
] = {}

CACHE_LOCK = Lock()


# =========================================================
# CLEANUP EXPIRED ENTRIES
# =========================================================

def cleanup_expired_entries() -> None:
    """
    Remove expired cache entries safely.
    """

    current_time = time.time()

    expired_keys = [

        key

        for key, entry in CACHE.items()

        if entry.expires_at < current_time
    ]

    for key in expired_keys:

        del CACHE[key]

        increment_counter(
            "cache_evictions"
        )

    if expired_keys:

        LOGGER.info(
            f"Removed {len(expired_keys)} "
            f"expired cache entries"
        )


# =========================================================
# CACHE SIZE CONTROL
# =========================================================

def enforce_cache_limit() -> None:
    """
    Prevent unbounded memory growth.
    """

    if len(CACHE) < MAX_CACHE_SIZE:

        return

    oldest_key = min(
        CACHE,
        key=lambda key: CACHE[key].created_at
    )

    del CACHE[oldest_key]

    increment_counter(
        "cache_evictions"
    )

    LOGGER.warning(
        f"Evicted oldest cache entry: "
        f"{oldest_key}"
    )


# =========================================================
# CACHE WRITE
# =========================================================

def set_cache(
    key: str,
    value: Any,
    ttl_seconds: int = DEFAULT_TTL_SECONDS
) -> None:
    """
    Store value in cache safely.
    """

    with CACHE_LOCK:

        cleanup_expired_entries()

        enforce_cache_limit()

        current_time = time.time()

        CACHE[key] = CacheEntry(
            value=value,
            created_at=current_time,
            expires_at=(
                current_time
                + ttl_seconds
            )
        )

    increment_counter(
        "cache_writes"
    )

    LOGGER.info(
        f"Cache stored for key: {key}"
    )


# =========================================================
# CACHE READ
# =========================================================

def get_cache(
    key: str
) -> Any | None:
    """
    Retrieve cache value safely.
    """

    with CACHE_LOCK:

        cleanup_expired_entries()

        entry = CACHE.get(key)

        if not entry:

            increment_counter(
                "cache_misses"
            )

            LOGGER.info(
                f"Cache miss: {key}"
            )

            return None

        current_time = time.time()

        if entry.expires_at < current_time:

            del CACHE[key]

            increment_counter(
                "cache_expired"
            )

            LOGGER.info(
                f"Cache expired: {key}"
            )

            return None

        increment_counter(
            "cache_hits"
        )

        LOGGER.info(
            f"Cache hit: {key}"
        )

        return entry.value


# =========================================================
# CACHE INVALIDATION
# =========================================================

def clear_cache() -> None:
    """
    Clear entire cache safely.
    """

    with CACHE_LOCK:

        CACHE.clear()

    LOGGER.warning(
        "Entire cache cleared"
    )


# =========================================================
# CACHE METRICS
# =========================================================

def get_cache_stats() -> dict[str, Any]:
    """
    Return cache diagnostics.
    """

    with CACHE_LOCK:

        cleanup_expired_entries()

        total_entries = len(CACHE)

    return {

        "total_entries":
            total_entries,

        "max_cache_size":
            MAX_CACHE_SIZE,

        "default_ttl_seconds":
            DEFAULT_TTL_SECONDS
    }