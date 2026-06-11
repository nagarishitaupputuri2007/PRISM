# backend/middleware/request_logging.py
# PRISM 2.6 — Request Logging Middleware

"""
Centralized request logging middleware.

Responsibilities:
- request tracing
- request timing
- request IDs
- structured API logs
- latency monitoring

This layer DOES NOT:
- execute business logic
- handle AI workflows
- contain routing logic

Those responsibilities belong to:
- routers/
- engines/
"""

import time
import uuid

from fastapi import Request
from starlette.middleware.base import (
    BaseHTTPMiddleware
)
from starlette.responses import Response

from backend.core.logging import (
    get_logger
)


# =========================================================
# LOGGER
# =========================================================

LOGGER = get_logger(__name__)


# =========================================================
# REQUEST LOGGING MIDDLEWARE
# =========================================================

class RequestLoggingMiddleware(
    BaseHTTPMiddleware
):
    """
    Logs:
    - request method
    - request path
    - response status
    - latency
    - request ID
    """

    async def dispatch(
        self,
        request: Request,
        call_next
    ) -> Response:

        request_id = str(
            uuid.uuid4()
        )[:8]

        request_start = (
            time.perf_counter()
        )

        LOGGER.info(
            f"[Request {request_id}] "
            f"Started "
            f"{request.method} "
            f"{request.url.path}"
        )

        try:

            response = await call_next(
                request
            )

            duration = (
                time.perf_counter()
                - request_start
            )

            LOGGER.info(
                f"[Request {request_id}] "
                f"Completed "
                f"{response.status_code} "
                f"in {duration:.2f}s"
            )

            response.headers[
                "X-Request-ID"
            ] = request_id

            return response

        except Exception as error:

            duration = (
                time.perf_counter()
                - request_start
            )

            LOGGER.exception(
                f"[Request {request_id}] "
                f"Failed after "
                f"{duration:.2f}s: "
                f"{error}"
            )

            raise