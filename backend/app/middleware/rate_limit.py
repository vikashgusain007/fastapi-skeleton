import time
from fastapi import Request, Response, status
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from core.config import settings
from loguru import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis-backed sliding window rate limiter.
    Limits requests based on the client IP address.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next) -> Response:
        # Exclude internal / system routes from rate limiting
        if request.url.path in (
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ):
            return await call_next(request)

        try:
            # Connect to Redis
            redis_client: Redis = Redis.from_url(
                settings.REDIS_URL, decode_responses=True
            )

            # Identify client by IP
            client_ip = request.client.host if request.client else "unknown"
            key = f"rate_limit:{client_ip}"

            now = time.time()
            clear_before = now - self.window_seconds

            # Execute transaction pipeline for sliding window calculation
            async with redis_client.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(key, 0, clear_before)
                pipe.zcard(key)
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, self.window_seconds)
                _, request_count, _, _ = await pipe.execute()

            await redis_client.aclose()

            # Verify limit
            if request_count > self.max_requests:
                logger.warning(
                    f"Rate limit exceeded for IP: {client_ip}. Requests: {request_count}/{self.max_requests}"
                )
                return Response(
                    content=(
                        '{"success": false, "message": "Too many requests. Please try again later.", "data": null}'
                    ),
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json",
                )

        except Exception as exc:
            # Fallback gracefully if Redis is down/unavailable
            logger.error(
                f"Rate limiting failure (Redis error): {exc}. Passing request through."
            )

        return await call_next(request)
