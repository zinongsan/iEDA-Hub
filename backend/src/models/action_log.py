"""操作日志模型"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.session import Base


class ActionLog(Base):
    """用户操作日志"""
    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 用户信息
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 操作信息
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # 操作类型
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 资源类型
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # 资源ID

    # 请求信息
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv4/IPv6
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)  # User-Agent

    # 详细信息（JSON格式）
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # 关联用户
    user = relationship("User", backref="action_logs", lazy="joined")

    # 复合索引：user_id + created_at（常用查询组合）
    __table_args__ = (
        {"comment": "用户操作日志表"},
    )
