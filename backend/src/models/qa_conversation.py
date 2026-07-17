"""对话会话模型"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.session import Base


class QAConversation(Base):
    """AI对话会话表"""
    __tablename__ = "qa_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 用户信息
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 会话信息
    session_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="前端生成的会话ID（UUID），用于关联多轮对话"
    )
    conversation_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="对话标题，可从第一个问题自动生成或用户编辑"
    )

    # 元数据（避免使用metadata保留字）
    extra_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="扩展字段（设备信息、浏览器等）"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # 关联
    user = relationship("User", backref="qa_conversations", lazy="joined")
    messages = relationship("QAMessage", back_populates="conversation", cascade="all, delete-orphan")

    # 复合索引
    __table_args__ = (
        {"comment": "AI对话会话表"},
    )
