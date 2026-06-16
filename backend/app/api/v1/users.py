from fastapi import APIRouter, Depends
from core.dependencies import RoleChecker, get_current_active_user
from db.models.user import User, UserRole
from schemas.response import APIResponse
from schemas.user import UserResponse

router = APIRouter()


@router.get("/me", response_model=APIResponse[UserResponse])
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> APIResponse[UserResponse]:
    """
    Retrieve the current logged-in user profile.
    """
    return APIResponse(
        success=True,
        message="User profile retrieved successfully",
        data=UserResponse.from_orm(current_user),
    )


@router.get("/admin-only", response_model=APIResponse[UserResponse])
async def read_admin_only(
    current_user: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> APIResponse[UserResponse]:
    """
    Sample admin-only endpoint to verify Role-Based Access Control (RBAC).
    """
    return APIResponse(
        success=True,
        message="Admin access verified successfully",
        data=UserResponse.from_orm(current_user),
    )
