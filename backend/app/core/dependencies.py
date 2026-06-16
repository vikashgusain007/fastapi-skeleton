from typing import AsyncGenerator, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings
from core.security import decode_token
from db.models.user import User, UserRole
from db.session import async_session_maker
from services.user import user_service

# Defines OAuth2 scheme. Matches OAuth2 password flow.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generating async SQLAlchemy sessions.
    Automatically rolls back / commits sessions.
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[Redis, None]:
    """
    Dependency generating a connection to Redis.
    """
    client: Redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Extracts the user ID from JWT token and fetches the User from the database.
    """
    try:
        payload = decode_token(token, is_refresh=False)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = await user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensures that the current user is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


class RoleChecker:
    """
    RBAC dependency constructor. Checks whether the current user is active and
    possesses one of the allowed roles.
    """

    def __init__(self, allowed_roles: List[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(
        self, current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have permission to perform this action",
            )
        return current_user
