"""User 相关 Pydantic Schema"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from ..models.user import UserTier


class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    tier: UserTier
    description: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    username: str
    tier: UserTier
    is_admin: bool
    is_active: bool
    email_verified: bool = True

    # 个人信息字段
    real_name: str | None = None
    role: str | None = None
    student_id: str | None = None
    school: str | None = None
    major: str | None = None  # 专业（学生）
    college: str | None = None  # 学院（老师）
    phone: str | None = None
    avatar_url: str | None = None  # 头像URL
    profile_completed: bool = False

    # 通知偏好
    notification_email: bool = True
    notification_system: bool = True
    notification_course: bool = True
    notification_announcement: bool = True

    group: GroupOut | None = None
    created_at: datetime
    last_login_at: datetime | None = None


class ProfileCompleteRequest(BaseModel):
    """完善个人信息请求"""
    real_name: str = Field(..., min_length=2, max_length=50, description="真实姓名")
    role: Literal["student", "teacher"] = Field(..., description="角色")
    student_id: str | None = Field(None, max_length=50, description="学号（学生必填）")
    school: str = Field(..., max_length=100, description="学校（必填）")
    major: str | None = Field(None, max_length=100, description="专业（学生必填）")
    college: str | None = Field(None, max_length=100, description="学院（老师必填）")
    email: EmailStr = Field(..., description="邮箱（必填）")


class ProfileUpdateRequest(BaseModel):
    """更新个人信息请求（可选字段）"""
    real_name: str | None = Field(None, min_length=2, max_length=50)
    role: str | None = Field(None, pattern="^(student|teacher)$")
    student_id: str | None = Field(None, max_length=50)
    school: str | None = Field(None, max_length=100)
    major: str | None = Field(None, max_length=100)
    college: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, pattern=r"^1[3-9]\d{9}$")
    email: EmailStr | None = Field(None, description="邮箱")


class NotificationSettingsRequest(BaseModel):
    """通知设置请求"""
    notification_email: bool | None = None
    notification_system: bool | None = None
    notification_course: bool | None = None
    notification_announcement: bool | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
