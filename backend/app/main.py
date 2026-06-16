from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.exceptions import HTTPException as StarletteHTTPException
from api.router import api_router
from api.v1.health import health_check
from core.config import settings
from core.dependencies import get_db, get_redis
from core.logging import setup_logging
from middleware.rate_limit import RateLimitMiddleware
from middleware.request_log import RequestLogMiddleware
from middleware.security import SecurityHeadersMiddleware
from loguru import logger


def setup_otel(app: FastAPI) -> None:
    """
    Initialize OpenTelemetry tracing if dependencies are present and setup succeeds.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create(
            attributes={"service.name": settings.OTEL_SERVICE_NAME}
        )
        provider = TracerProvider(resource=resource)
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True
        )
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        # Instruments FastAPI
        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry tracing successfully instrumented.")
    except Exception as exc:
        logger.warning(f"OpenTelemetry tracing could not be initialized: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan handler checking connection to resources.
    """
    setup_logging()
    logger.info("Initializing application startup sequence...")

    # Pre-ping db connection to verify setup
    try:
        async for session in get_db():
            from sqlalchemy import text

            await session.execute(text("SELECT 1"))
            logger.info("Connection to PostgreSQL verified successfully.")
            break
    except Exception as exc:
        logger.error(f"Failed to connect to PostgreSQL database on startup: {exc}")

    # Pre-ping Redis connection
    try:
        async for redis in get_redis():
            await redis.ping()
            logger.info("Connection to Redis verified successfully.")
            break
    except Exception as exc:
        logger.error(f"Failed to connect to Redis on startup: {exc}")

    yield

    logger.info("Shutting down application...")


# FastAPI application initialization
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade FastAPI boiler-plate backend.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Custom Middlewares (applied in reverse order of execution)
# 4. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 3. Rate Limit Middleware
app.add_middleware(
    RateLimitMiddleware, max_requests=100, window_seconds=60
)

# 2. Request Logging Middleware
app.add_middleware(RequestLogMiddleware)

# 1. CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Prometheus metrics setup
import sys

if "pytest" not in sys.modules:
    Instrumentator().instrument(app).expose(
        app,
        endpoint=settings.PROMETHEUS_METRICS_PATH,
        tags=["Observability"],
    )

# OpenTelemetry Tracing setup
if "pytest" not in sys.modules:
    setup_otel(app)

# Include API Router version 1
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root level health endpoint (aliases GET /health)
@app.get(
    "/health",
    tags=["System Health"],
    summary="Validate API health",
    description="Validate active status of database and redis storage.",
)
async def root_health_check(
    db=Depends(get_db), redis=Depends(get_redis)
):
    from fastapi import Response

    response = Response()
    return await health_check(response, db, redis)


# Exception Handlers to standardize JSON response outputs
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = exc.errors()
    error_messages = []
    for err in errors:
        loc = " -> ".join(str(p) for p in err.get("loc", []))
        msg = err.get("msg", "Validation error")
        error_messages.append(f"{loc}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation failed: " + "; ".join(error_messages),
            "data": None,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail,
            "data": None,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception(f"Unhandled exception intercepted: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected error occurred. Please try again later.",
            "data": None,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
