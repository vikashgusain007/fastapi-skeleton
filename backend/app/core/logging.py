import logging
import sys
from contextvars import ContextVar
from loguru import logger
from core.config import settings

# Correlation ID Context Variable
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


class InterceptHandler(logging.Handler):
    """
    Default handler from python logging to loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def custom_serializer(record):
    """
    Serializes a log record into a structured JSON string.
    """
    import json

    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        "correlation_id": correlation_id.get(),
    }
    if record["exception"]:
        subset["exception"] = {
            "type": str(record["exception"].type),
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback,
        }
    return json.dumps(subset)


def custom_format(record):
    """
    Formats the log output based on environment.
    """
    if settings.ENVIRONMENT in ("prod", "stage"):
        # For production / staging, we use structured JSON logging
        record["extra"]["serialized"] = custom_serializer(record)
        return "{extra[serialized]}\n"
    else:
        # For development, we use a clean colored human-readable log
        cid = correlation_id.get()
        cid_str = f" [{cid}]" if cid else ""
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            f"<level>{{message}}</level>{cid_str}\n"
        )


def setup_logging() -> None:
    # Disable uvicorn's default access/error handlers as we'll intercept them
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.error").handlers = []

    # Intercept standard logging with our intercept handler
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Intercept specific third party logs
    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi", "sqlalchemy"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    # Remove all default loguru handlers
    logger.remove()

    # Configure Loguru output
    logger.add(
        sys.stdout,
        enqueue=True,
        backtrace=True,
        diagnose=settings.DEBUG,
        format=custom_format,
        level="DEBUG" if settings.DEBUG else "INFO",
    )
