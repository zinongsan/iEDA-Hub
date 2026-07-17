"""对话消息模型"""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, CheckConstraint, ARRAY, func, NUMERIC
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.session import Base


class QAMessage(Base):
    """AI对话消息表"""
    __tablename__ = "qa_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 关联会话
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("qa_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 消息信息
    message_role: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="'user' 或 'assistant'"
    )
    message_content: Mapped[str] = mapped_column(Text, nullable=False)

    # AI回答相关（仅message_role='assistant'时有值）
    sources: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="参考来源（RAG检索的文档片段）"
    )
    tokens_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_yuan: Mapped[Decimal | None] = mapped_column(
        NUMERIC(12, 6),  # 最大支持999999.999999元（12位数字，6位小数）
        nullable=True,
        comment="成本（元）"
    )
    response_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="响应时间（毫秒）"
    )
    retrieval_mode: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="检索模式（vector/keyword）"
    )

    # 知识点标签
    knowledge_tags: Mapped[list[str] | None] = mapped_column(
        ARRAY(String),
        nullable=True,
        comment="知识点标签数组（如['SDC约束','时序分析']）"
    )

    # 质量评估
    user_rating: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="用户评分1-5星"
    )
    is_corrected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        index=True
    )
    correction_id: Mapped[int | None] = mapped_column(
        ForeignKey("qa_corrections.id", ondelete="SET NULL"),
        nullable=True
    )

    # 追问标记
    is_followup: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        comment="是否是追问"
    )
    parent_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("qa_messages.id", ondelete="SET NULL"),
        nullable=True,
        comment="追问的父消息ID"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )

    # 关联
    conversation = relationship("QAConversation", back_populates="messages")
    correction = relationship("QACorrection", foreign_keys="[QACorrection.message_id]", back_populates="message", uselist=False)
    parent_message = relationship("QAMessage", remote_side=[id], foreign_keys=[parent_message_id])
    rating = relationship("QARating", back_populates="message", uselist=False)

    # 约束
    __table_args__ = (
        CheckConstraint("user_rating IS NULL OR (user_rating BETWEEN 1 AND 5)", name="check_user_rating"),
        CheckConstraint("message_role IN ('user', 'assistant')", name="check_message_role"),
        {"comment": "AI对话消息表"},
    )
