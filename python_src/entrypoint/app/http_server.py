"""HTTP server setup and configuration."""

import structlog
from fastapi import FastAPI

from internal.router.handlers import create_api_router
from internal.router.middleware import LoggingMiddleware, RequestIDMiddleware


def configure_logging() -> structlog.BoundLogger:
    """Configure structured logging for the application."""
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Create root logger
    logger = structlog.get_logger()
    return logger.bind(service="workshop", env="production")


def create_app(logger: structlog.BoundLogger | None = None) -> FastAPI:
    """Create and configure FastAPI application."""
    if logger is None:
        logger = configure_logging()

    app = FastAPI(title="Workshop API", version="1.0.0", docs_url="/docs", redoc_url="/redoc")

    # Add middleware (order matters - first added is outermost)
    app.add_middleware(LoggingMiddleware, logger=logger)
    app.add_middleware(RequestIDMiddleware)

    # Add API routes
    api_router = create_api_router()
    app.include_router(api_router)

    return app


app = create_app()
