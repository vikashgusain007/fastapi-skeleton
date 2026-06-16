from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.dependencies import get_db
from core.security import create_access_token, create_refresh_token
from schemas.response import APIResponse
from schemas.token import LoginRequest, Token, TokenRefreshRequest
from schemas.user import UserCreate, UserResponse
from services.auth import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_in: UserCreate, db: AsyncSession = Depends(get_db)
) -> APIResponse[UserResponse]:
    """
    Register a new user account.
    """
    user = await auth_service.register(db, user_in=user_in)
    return APIResponse(
        success=True,
        message="User successfully registered",
        data=UserResponse.from_orm(user),
    )


@router.post("/login", response_model=APIResponse[Token])
async def login(
    login_req: LoginRequest, db: AsyncSession = Depends(get_db)
) -> APIResponse[Token]:
    """
    Authenticate a user and return access and refresh JWT tokens.
    """
    user = await auth_service.authenticate(
        db, email=login_req.email, password=login_req.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return APIResponse(
        success=True,
        message="Login successful",
        data=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        ),
    )


@router.post("/refresh", response_model=APIResponse[Token])
async def refresh_token(
    refresh_req: TokenRefreshRequest, db: AsyncSession = Depends(get_db)
) -> APIResponse[Token]:
    """
    Generate new access and refresh tokens using a valid refresh token.
    """
    tokens = await auth_service.refresh_tokens(
        db, refresh_token=refresh_req.refresh_token
    )
    return APIResponse(
        success=True,
        message="Token refreshed successfully",
        data=tokens,
    )
