# backend/main.py
# PRISM 2.5 — Enterprise Application Entry Point

"""
PRISM Backend Application

Responsibilities:
- initialize FastAPI app
- configure middleware
- register routers
- expose health endpoints
- configure observability
- manage application lifecycle

This layer DOES NOT:
- execute AI workflows
- contain business logic
- calculate scoring
- perform domain reasoning

Those responsibilities belong to:
- routers/
- engines/
- utils/
"""

import os
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import (
    FastAPI,
    Request,
    Response
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

from fastapi.responses import (
    JSONResponse
)

from backend.routers.analyze import (
    router as analyze_router
)

from backend.services.cache import (
    clear_cache,
    get_cache_stats
)

from backend.core.logging import (
    get_logger
)

from backend.core.metrics import (
    get_metrics
)


# =========================================================
# APPLICATION METADATA
# =========================================================

APP_NAME = "PRISM AI"

APP_VERSION = "2.5.0"

APP_DESCRIPTION = (
    "AI-powered product intelligence "
    "and UX analysis platform."
)

ENVIRONMENT = os.getenv(
    "ENVIRONMENT",
    "development"
)


# =========================================================
# LOGGER
# =========================================================

LOGGER = get_logger(__name__)


# =========================================================
# APPLICATION LIFECYCLE
# =========================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI
):
    """
    Manage application startup
    and shutdown lifecycle.
    """

    LOGGER.info(
        f"Starting {APP_NAME} v{APP_VERSION}"
    )

    LOGGER.info(
        f"Environment: {ENVIRONMENT}"
    )

    LOGGER.info(
        "Initializing PRISM services"
    )

    yield

    LOGGER.info(
        "Beginning graceful shutdown"
    )

    LOGGER.info(
        f"Shutting down {APP_NAME}"
    )

    LOGGER.info(
        "Shutdown completed successfully"
    )


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "System",
            "description": (
                "System monitoring and "
                "health endpoints."
            )
        },
        {
            "name": "Observability",
            "description": (
                "Metrics, cache diagnostics, "
                "and operational monitoring."
            )
        },
        {
            "name": "PRISM Analysis",
            "description": (
                "AI-powered product "
                "intelligence analysis."
            )
        }
    ]
)


# =========================================================
# CORS CONFIGURATION
# =========================================================

ALLOWED_ORIGINS = [

    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# REQUEST TIMING MIDDLEWARE
# =========================================================

@app.middleware("http")
async def request_timing_middleware(
    request: Request,
    call_next: Callable[
        [Request],
        Awaitable[Response]
    ]
) -> Response:
    """
    Measure request execution time.
    """

    request_start = (
        time.perf_counter()
    )

    response = await call_next(
        request
    )

    duration = (
        time.perf_counter()
        - request_start
    )

    LOGGER.info(
        f"{request.method} "
        f"{request.url.path} "
        f"completed in "
        f"{duration:.2f}s "
        f"with status "
        f"{response.status_code}"
    )

    response.headers[
        "X-Process-Time"
    ] = f"{duration:.2f}"

    return response


# =========================================================
# GLOBAL ERROR HANDLER
# =========================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    error: Exception
) -> JSONResponse:
    """
    Catch unexpected application failures.
    """

    LOGGER.exception(
        f"Unhandled application error: "
        f"{error}"
    )

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": (
                "Internal server error"
            )
        }
    )


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get(
    "/",
    tags=["System"]
)
async def root() -> dict[str, str]:
    """
    Root system endpoint.
    """

    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "status": "running",
        "message": (
            "PRISM AI backend is operational"
        )
    }


# =========================================================
# HEALTH CHECK ENDPOINT
# =========================================================

@app.get(
    "/health",
    tags=["System"]
)
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    """

    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "status": "healthy"
    }


# =========================================================
# METRICS ENDPOINT
# =========================================================

@app.get(
    "/metrics",
    tags=["Observability"]
)
async def metrics_endpoint() -> dict[str, Any]:
    """
    Return application metrics.
    """

    LOGGER.info(
        "Metrics endpoint accessed"
    )

    return {
        "status": "success",
        "metrics": get_metrics()
    }


# =========================================================
# CACHE STATS ENDPOINT
# =========================================================

@app.get(
    "/cache/stats",
    tags=["Observability"]
)
async def cache_stats_endpoint() -> dict[str, Any]:
    """
    Return cache diagnostics.
    """

    LOGGER.info(
        "Cache stats endpoint accessed"
    )

    return {
        "status": "success",
        "cache": get_cache_stats()
    }


# =========================================================
# CACHE CLEAR ENDPOINT
# =========================================================

@app.post(
    "/cache/clear",
    tags=["Observability"]
)
async def cache_clear_endpoint() -> dict[str, str]:
    """
    Clear cache manually.
    """

    clear_cache()

    LOGGER.warning(
        "Cache cleared manually"
    )

    return {
        "status": "success",
        "message": (
            "Cache cleared successfully"
        )
    }


# =========================================================
# ROUTER REGISTRATION
# =========================================================

app.include_router(
    analyze_router,
    prefix="/api/v1"
)