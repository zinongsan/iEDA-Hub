"""高级用户专属示例接口"""
from fastapi import APIRouter

from ...core.deps import PremiumUser

router = APIRouter(prefix="/premium", tags=["premium"])


@router.get("/feature")
async def premium_feature(user: PremiumUser) -> dict:
    return {
        "message": "你已解锁高级功能",
        "user": user.username,
        "tier": user.tier.value,
    }
