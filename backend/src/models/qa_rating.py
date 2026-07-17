"""用户评分模型"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, CheckConstraint, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.session import Base


class QARating(Base):
    """用户对AI答案的评分表"""
    __tablename__ = "qa_ratings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 关联消息
    message_id: Mapped[int] = mapped_column(
        ForeignKey("qa_messages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 每条消息只能评分一次
        index=True
    )

    # 评分维度
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False, comment="总体评分 1-5")
    accuracy_rating: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="准确性 1-5")
    completeness_rating: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="完整性 1-5")
    clarity_rating: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="清晰度 1-5")

    # 反馈
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="文字反馈")

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # 关联
    message = relationship("QAMessage", back_populates="rating")

    # 约束
    __table_args__ = (
        CheckConstraint("overall_rating BETWEEN 1 AND 5", name="check_overall_rating"),
        CheckConstraint("accuracy_rating IS NULL OR (accuracy_rating BETWEEN 1 AND 5)", name="check_accuracy_rating"),
        CheckConstraint("completeness_rating IS NULL OR (completeness_rating BETWEEN 1 AND 5)", name="check_completeness_rating"),
        CheckConstraint("clarity_rating IS NULL OR (clarity_rating BETWEEN 1 AND 5)", name="check_clarity_rating"),
        {"comment": "用户对AI答案的评分表"},
    )
