import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from core.logging import correlation_id
from loguru import logger


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware that captures execution time and status codes for requests,
    generates or extracts X-Correlation-ID, and logs the transactions.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Determine or generate the Correlation ID
        corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        correlation_id.set(corr_id)

        # Log incoming request
        logger.info(
            f"Request started: {request.method} {request.url.path}"
            f"{f'?{request.url.query}' if request.url.query else ''}"
        )

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            duration = (time.perf_counter() - start_time) * 1000
            logger.exception(
                f"Request failed: {request.method} {request.url.path} - "
                f"Failed in {duration:.2f}ms - Exception: {exc}"
            )
            raise exc

        duration = (time.perf_counter() - start_time) * 1000
        # Set correlation ID in response headers
        response.headers["X-Correlation-ID"] = corr_id

        # Log outgoing response
        logger.info(
            f"Request finished: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Completed in {duration:.2f}ms"
        )

        return response
