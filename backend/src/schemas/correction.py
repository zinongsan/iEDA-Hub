"""答案纠正相关的数据模型"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------- 请求模型 ----------
class CorrectionCreate(BaseModel):
    """创建纠正记录"""
    message_id: int = Field(..., description="被纠正的消息ID")
    original_answer: str = Field(..., description="原始AI答案")
    corrected_answer: str = Field(..., min_length=1, description="纠正后的答案")
    correction_reason: Optional[str] = Field(None, max_length=500, description="纠正原因")


class CorrectionUpdate(BaseModel):
    """更新纠正记录"""
    corrected_answer: Optional[str] = Field(None, min_length=1, description="纠正后的答案")
    correction_reason: Optional[str] = Field(None, max_length=500, description="纠正原因")


class CorrectionReview(BaseModel):
    """审核纠正记录"""
    status: str = Field(..., description="审核结果: approved/rejected")
    review_reason: Optional[str] = Field(None, max_length=500, description="审核意见")
    quality_score: Optional[int] = Field(None, ge=0, le=10, description="质量评分0-10，用于计算额外积分")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "approved",
                "review_reason": "纠正准确，对知识库有帮助",
                "quality_score": 5
            }
        }


# ---------- 响应模型 ----------
class UserBrief(BaseModel):
    """用户简要信息"""
    id: int
    username: str
    email: str
    role: Optional[str] = None

    class Config:
        from_attributes = True


class MessageBrief(BaseModel):
    """消息简要信息"""
    id: int
    message_role: str
    message_content: str
    user_rating: Optional[int] = None
    sources: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationBrief(BaseModel):
    """对话简要信息"""
    id: int
    conversation_title: str
    created_at: datetime

    class Config:
        from_attributes = True


class CorrectionDetail(BaseModel):
    """纠正详情"""
    id: int
    message_id: int
    original_answer: str
    corrected_answer: str
    correction_reason: Optional[str] = None

    # 状态信息
    status: str = Field(..., description="pending/approved/rejected")
    reward_points: int = Field(default=0, description="奖励积分")

    # 时间信息
    created_at: datetime
    reviewed_at: Optional[datetime] = None

    # 关联信息
    message: Optional[MessageBrief] = None
    conversation: Optional[ConversationBrief] = None
    corrector: Optional[UserBrief] = None
    reviewer: Optional[UserBrief] = None

    # 置信度评分（根据多个因素计算）
    confidence_score: Optional[int] = Field(None, ge=0, le=100, description="置信度0-100")

    class Config:
        from_attributes = True

    @classmethod
    def model_validate(cls, obj):
        """自定义验证，处理关联对象"""
        data = {
            "id": obj.id,
            "message_id": obj.message_id,
            "original_answer": obj.original_answer,
            "corrected_answer": obj.corrected_answer,
            "correction_reason": obj.correction_reason,
            "status": obj.status,
            "reward_points": obj.reward_points,
            "created_at": obj.created_at,
            "reviewed_at": obj.reviewed_at,
        }

        # 处理message关联
        if hasattr(obj, 'message') and obj.message:
            data["message"] = MessageBrief.model_validate(obj.message)

            # 处理conversation关联（通过message）
            if hasattr(obj.message, 'conversation') and obj.message.conversation:
                data["conversation"] = ConversationBrief.model_validate(obj.message.conversation)

            # 计算置信度
            msg = obj.message
            if msg.user_rating:
                if msg.user_rating <= 2:
                    data["confidence_score"] = msg.user_rating * 10
                elif msg.user_rating == 3:
                    data["confidence_score"] = 50
                else:
                    data["confidence_score"] = msg.user_rating * 20 - 10
            elif msg.sources:
                data["confidence_score"] = 60
            else:
                data["confidence_score"] = 30

        # 处理corrector关联
        if hasattr(obj, 'corrector') and obj.corrector:
            data["corrector"] = UserBrief.model_validate(obj.corrector)

        # 处理reviewer关联
        if hasattr(obj, 'reviewer') and obj.reviewer:
            data["reviewer"] = UserBrief.model_validate(obj.reviewer)

        return cls(**data)


class CorrectionList(BaseModel):
    """纠正列表响应"""
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")
    items: list[CorrectionDetail] = Field(default_factory=list, description="纠正列表")


class CorrectionStats(BaseModel):
    """审核进度统计"""
    total: int = Field(..., description="总纠正数")
    pending: int = Field(..., description="待审核数")
    approved: int = Field(..., description="已通过数")
    rejected: int = Field(..., description="已拒绝数")
    reviewed: int = Field(..., description="已审核数（通过+拒绝）")
    today_new: int = Field(..., description="今日新增数")
    avg_review_hours: float = Field(..., description="平均审核时长（小时）")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 150,
                "pending": 25,
                "approved": 100,
                "rejected": 25,
                "reviewed": 125,
                "today_new": 8,
                "avg_review_hours": 12.5
            }
        }
