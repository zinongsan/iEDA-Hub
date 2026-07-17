"""管理员后台 Schema"""
from pydantic import BaseModel, EmailStr, Field

from ..models.user import UserTier


class AdminUserUpdate(BaseModel):
    tier: UserTier | None = None
    is_active: bool | None = None
    is_admin: bool | None = None
    group_id: int | None = None


class GroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    tier: UserTier
    description: str | None = None


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    tier: UserTier | None = None
    description: str | None = None


class AdminCreateUser(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    tier: UserTier = UserTier.NORMAL
    is_admin: bool = False
    group_id: int | None = None


class AssignGroupRequest(BaseModel):
    user_ids: list[int]
    group_id: int
