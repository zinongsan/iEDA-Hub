"""Group 模型 - 用户组（普通组 / 高级组），分配组即决定 tier"""
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.session import Base
from .user import UserTier


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tier: Mapped[UserTier] = mapped_column(Enum(UserTier, name="user_tier"), nullable=False)

    users = relationship("User", back_populates="group", lazy="selectin")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
