"""
Query Timing Middleware for FastAPI

Logs slow queries and provides performance monitoring.
Logs requests that exceed the configured threshold.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logger for slow queries
logger = logging.getLogger("ocean.performance")


class QueryTimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track and log API request timing.

    Logs requests that exceed the slow_query_threshold to help
    identify performance bottlenecks.
    """

    def __init__(
        self,
        app: ASGIApp,
        slow_query_threshold_ms: float = 100.0
    ):
        """
        Initialize timing middleware.

        Args:
            app: ASGI application
            slow_query_threshold_ms: Log queries slower than this (default: 100ms)
        """
        super().__init__(app)
        self.slow_query_threshold_ms = slow_query_threshold_ms

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process request and measure timing.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            Response with timing header added
        """
        # Record start time
        start_time = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Add timing header to response
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

        # Log slow queries
        if duration_ms > self.slow_query_threshold_ms:
            logger.warning(
                f"Slow query detected: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms (threshold: {self.slow_query_threshold_ms}ms)",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "query_params": str(request.query_params),
                    "client": request.client.host if request.client else "unknown"
                }
            )
        else:
            # Log all queries at debug level
            logger.debug(
                f"{request.method} {request.url.path} completed in {duration_ms:.2f}ms"
            )

        return response
