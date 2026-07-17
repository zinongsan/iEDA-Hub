"""API路由注册"""
from fastapi import APIRouter

from .v1 import admin, auth, premium, users, logs

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/v1/auth")
api_router.include_router(users.router, prefix="/v1")
api_router.include_router(admin.router, prefix="/v1/admin")
api_router.include_router(premium.router, prefix="/v1/premium")
api_router.include_router(logs.router, prefix="/v1")
