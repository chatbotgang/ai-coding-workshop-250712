"""HTTP route handlers for the application."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from entrypoint.app.settings import AppConfig
from internal.domain.common.requestid import get_request_id_or_new

# Global config instance for health check
_config = AppConfig()


def create_api_router() -> APIRouter:
    """Create and configure the API router with all endpoints."""
    router = APIRouter(prefix="/api")

    # Create v1 router
    v1_router = APIRouter(prefix="/v1")

    # Add health check endpoint
    v1_router.add_api_route(
        "/health", health_check, methods=["GET"], status_code=status.HTTP_200_OK, response_class=JSONResponse
    )

    # Include v1 router in main router
    router.include_router(v1_router)

    return router


async def health_check() -> JSONResponse:
    """Health check endpoint."""
    request_id = get_request_id_or_new()

    response_data = {"status": "healthy", "env": _config.env, "request_id": request_id}

    return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)
