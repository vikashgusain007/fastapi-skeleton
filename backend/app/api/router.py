from fastapi import APIRouter
from api.v1 import auth, health, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(health.router, prefix="/health", tags=["System Health"])
