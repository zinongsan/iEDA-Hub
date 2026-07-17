"""User 模型 - 包含分级 (tier) 与管理员标志"""
import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.session import Base


class UserTier(str, enum.Enum):
    NORMAL = "normal"
    PREMIUM = "premium"


class UserRole(str, enum.Enum):
    """用户角色"""
    STUDENT = "student"
    TEACHER = "teacher"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    tier: Mapped[UserTier] = mapped_column(
        Enum(UserTier, name="user_tier"), default=UserTier.NORMAL, nullable=False, index=True
    )
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # 邮箱是否已验证（注册时 False，点验证链接后 True）。存量用户迁移时默认 True。
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="true", nullable=False)
    # 手机号是否已验证（通过短信验证码注册后自动为 True）
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)

    # 个人信息扩展字段
    real_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "student" 或 "teacher"
    student_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    school: Mapped[str | None] = mapped_column(String(100), nullable=True)
    major: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 专业（学生）
    college: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 学院（老师）
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)  # 头像URL
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    profile_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 通知偏好设置
    notification_email: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    notification_system: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    notification_course: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    notification_announcement: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)

    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id", ondelete="SET NULL"), nullable=True, index=True
    )
    group = relationship("Group", back_populates="users", lazy="joined")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # 改密码后写入时间；get_current_user 据此让改密前签发的旧令牌失效（注销其他会话）。NULL 表示不限。
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
