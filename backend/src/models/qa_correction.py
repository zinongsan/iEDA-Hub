"""答案纠正记录模型"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.session import Base


class QACorrection(Base):
    """AI答案纠正记录表"""
    __tablename__ = "qa_corrections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 关联消息
    message_id: Mapped[int] = mapped_column(
        ForeignKey("qa_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 纠正信息
    original_answer: Mapped[str] = mapped_column(Text, nullable=False, comment="原始AI答案")
    corrected_answer: Mapped[str] = mapped_column(Text, nullable=False, comment="纠正后的答案")
    correction_reason: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="纠正原因")

    # 纠正人信息
    corrected_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="纠正人（老师）"
    )

    # 审核状态
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        server_default="pending",
        nullable=False,
        index=True,
        comment="pending待审/approved通过/rejected拒绝"
    )
    reviewed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="审核人"
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # 积分奖励
    reward_points: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="老师获得的积分奖励"
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # 关联
    message = relationship("QAMessage", foreign_keys=[message_id], back_populates="correction", overlaps="correction")
    corrector = relationship("User", foreign_keys=[corrected_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        {"comment": "AI答案纠正记录表"},
    )
