"""日志相关Schema"""
from datetime import datetime
from pydantic import BaseModel, Field


class ActionLogOut(BaseModel):
    """日志输出"""
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    details: dict | None = None
    created_at: datetime

    # 关联用户信息
    username: str | None = None
    email: str | None = None


class ActionLogListResponse(BaseModel):
    """日志列表响应"""
    total: int
    page: int
    page_size: int
    items: list[ActionLogOut]
