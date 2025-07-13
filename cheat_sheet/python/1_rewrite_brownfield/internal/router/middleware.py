"""HTTP middleware for request processing."""

import time
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from internal.domain.common.requestid import get_request_id, new_request_id, set_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware for managing request IDs."""

    HEADER_X_REQUEST_ID = "X-Request-ID"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate request ID
        request_id = request.headers.get(self.HEADER_X_REQUEST_ID, "")
        if not request_id:
            request_id = new_request_id()

        # Set request ID in context
        set_request_id(request_id)

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers[self.HEADER_X_REQUEST_ID] = request_id

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""

    def __init__(self, app: ASGIApp, logger: structlog.BoundLogger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Skip health check to avoid polluting logs
        if request.url.path == "/api/v1/health":
            return await call_next(request)

        # Get request ID for logging context
        request_id = get_request_id()

        # Create request logger with context
        log = self.logger.bind(requestID=request_id, path=request.url.path, method=request.method, component="router")

        try:
            # Process request
            response = await call_next(request)

            # Calculate latency
            latency = time.time() - start_time

            # Log successful request
            log.info(
                "Request processed",
                status=response.status_code,
                latency=f"{latency:.6f}s",
                clientIP=request.client.host if request.client else "unknown",
                fullPath=str(request.url),
                userAgent=request.headers.get("User-Agent", ""),
            )

            return response

        except Exception as e:
            # Calculate latency
            latency = time.time() - start_time

            # Log error
            log.error(
                "Request failed",
                error=str(e),
                latency=f"{latency:.6f}s",
                clientIP=request.client.host if request.client else "unknown",
                fullPath=str(request.url),
                userAgent=request.headers.get("User-Agent", ""),
            )

            raise
