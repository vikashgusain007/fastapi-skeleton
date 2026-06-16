from fastapi import APIRouter, Depends, Response, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db, get_redis

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Health check endpoint verifying async database connection and Redis connection.
    Fails with 500 if dependencies are unreachable.
    """
    db_status = "connected"
    redis_status = "connected"
    healthy = True

    # Validate database connectivity
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
        healthy = False

    # Validate Redis connectivity
    try:
        await redis.ping()
    except Exception:
        redis_status = "disconnected"
        healthy = False

    if not healthy:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {
            "status": "unhealthy",
            "database": db_status,
            "redis": redis_status,
        }

    return {
        "status": "healthy",
        "database": db_status,
        "redis": redis_status,
    }
