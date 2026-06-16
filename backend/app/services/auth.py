from typing import Optional
from fastapi import HTTPException, status
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from db.models.user import User
from schemas.token import Token
from schemas.user import UserCreate
from services.user import user_service


class AuthService:
    """
    Service layer containing business logic for authentication and tokens.
    """

    async def authenticate(
        self, db: AsyncSession, email: str, password: str
    ) -> Optional[User]:
        """
        Authenticate a user by checking email and verifying password.
        """
        user = await user_service.get_by_email(db, email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def register(self, db: AsyncSession, *, user_in: UserCreate) -> User:
        """
        Register a new user. Throws exception if email is registered.
        """
        user = await user_service.get_by_email(db, user_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email already exists.",
            )
        return await user_service.create(db, obj_in=user_in)

    async def refresh_tokens(self, db: AsyncSession, refresh_token: str) -> Token:
        """
        Rotate access/refresh token pairs using a valid refresh token.
        """
        try:
            payload = decode_token(refresh_token, is_refresh=True)
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token subject",
                )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user = await user_service.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
            )

        return Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )


auth_service = AuthService()
