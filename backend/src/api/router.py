"""聚合 v1 路由"""
from fastapi import APIRouter

from .v1 import admin, auth, corrections, logs, premium, users, rag, analytics

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(premium.router)
api_router.include_router(admin.router)
api_router.include_router(logs.router)
api_router.include_router(corrections.router)
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(analytics.router, prefix="/rag", tags=["analytics"])
