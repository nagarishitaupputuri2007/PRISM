# backend/main.py
# PRISM 2.1 — Application Entry Point

"""
PRISM Backend Application

Responsibilities:
- initialize FastAPI app
- register API routers
- expose health endpoints
- configure application metadata
- configure startup logging

This layer DOES NOT:
- contain business logic
- execute AI workflows
- perform scoring
- contain engine logic

Those responsibilities belong to:
- routers/
- engines/
- utils/
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.analyze import router as analyze_router


# =========================================================
# LOGGING CONFIGURATION
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )
)

LOGGER = logging.getLogger(__name__)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="PRISM AI",
    description=(
        "AI-powered product intelligence and "
        "UX analysis platform."
    ),
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "System",
            "description": (
                "System monitoring and health endpoints."
            )
        },
        {
            "name": "PRISM Analysis",
            "description": (
                "AI-powered product intelligence analysis."
            )
        }
    ]
)


# =========================================================
# CORS CONFIGURATION
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# APPLICATION STARTUP EVENT
# =========================================================

@app.on_event("startup")
async def startup_event() -> None:

    LOGGER.info(
        "Starting PRISM AI Backend v2.1.0"
    )


# =========================================================
# APPLICATION SHUTDOWN EVENT
# =========================================================

@app.on_event("shutdown")
async def shutdown_event() -> None:

    LOGGER.info(
        "Shutting down PRISM AI Backend"
    )


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get(
    "/",
    tags=["System"]
)
async def root() -> dict[str, str]:

    return {
        "name": "PRISM AI",
        "version": "2.1.0",
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

    return {
        "name": "PRISM AI",
        "version": "2.1.0",
        "status": "healthy"
    }


# =========================================================
# ROUTER REGISTRATION
# =========================================================

app.include_router(
    analyze_router,
    prefix="/api/v1"
)