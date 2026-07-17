"""对话相关的Pydantic schemas"""
from datetime import datetime
from typing import Literal, Optional, Union
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


# ============================================
# QA Conversation Schemas
# ============================================

class ConversationCreate(BaseModel):
    """创建对话会话"""
    session_id: str = Field(..., max_length=64, description="前端生成的会话ID（UUID）")
    conversation_title: Optional[str] = Field(None, max_length=255, description="对话标题")
    metadata: Optional[dict] = Field(None, description="元数据（设备信息等）")


class ConversationOut(BaseModel):
    """对话会话输出"""
    id: int
    user_id: int
    session_id: str
    conversation_title: Optional[str]
    message_count: int = Field(0, description="消息数量")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """对话列表响应"""
    conversations: list[ConversationOut]
    total: int
    page: int
    page_size: int


# ============================================
# QA Message Schemas
# ============================================

class MessageCreate(BaseModel):
    """创建消息（用户提问）"""
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    session_id: str = Field(..., max_length=64, description="会话ID")
    is_followup: bool = Field(False, description="是否是追问")
    parent_message_id: Optional[int] = Field(None, description="父消息ID（追问时）")
    max_tokens: int = Field(500, ge=50, le=2000)
    temperature: float = Field(0.7, ge=0, le=1)


class MessageOut(BaseModel):
    """消息输出"""
    id: int
    conversation_id: int
    message_role: Literal["user", "assistant"]
    message_content: str
    sources: Optional[dict] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    tokens_total: Optional[int] = None
    cost_yuan: Optional[str] = None
    response_time_ms: Optional[int] = None
    retrieval_mode: Optional[str] = None
    knowledge_tags: Optional[list[str]] = None
    user_rating: Optional[int] = None
    is_corrected: bool = False
    is_followup: bool = False
    parent_message_id: Optional[int] = None
    created_at: datetime

    @field_validator('cost_yuan', mode='before')
    @classmethod
    def convert_decimal_to_str(cls, v):
        """将Decimal类型转换为字符串"""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return str(v)
        return v

    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    """对话详情响应"""
    conversation: ConversationOut
    messages: list[MessageOut]


class QAResponse(BaseModel):
    """AI问答响应（扩展版）"""
    # 原有字段
    answer: str = Field(..., description="AI生成的答案")
    sources: list[str] = Field(..., description="参考来源")
    tokens: dict = Field(..., description="token统计")
    cost: float = Field(..., description="成本（人民币）")
    retrieval_mode: str = Field(..., description="检索模式 keyword/vector")

    # 新增字段
    message_id: int = Field(..., description="消息ID")
    conversation_id: int = Field(..., description="对话ID")
    user_message_id: int = Field(..., description="用户消息ID")


# ============================================
# Rating Schemas
# ============================================

class RatingCreate(BaseModel):
    """创建评分"""
    overall_rating: int = Field(..., ge=1, le=5, description="总体评分 1-5")
    accuracy_rating: Optional[int] = Field(None, ge=1, le=5, description="准确性 1-5")
    completeness_rating: Optional[int] = Field(None, ge=1, le=5, description="完整性 1-5")
    clarity_rating: Optional[int] = Field(None, ge=1, le=5, description="清晰度 1-5")
    feedback_text: Optional[str] = Field(None, max_length=2000, description="文字反馈")


class RatingOut(BaseModel):
    """评分输出"""
    id: int
    message_id: int
    overall_rating: int
    accuracy_rating: Optional[int]
    completeness_rating: Optional[int]
    clarity_rating: Optional[int]
    feedback_text: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Correction Schemas
# ============================================

class CorrectionCreate(BaseModel):
    """创建纠正"""
    corrected_answer: str = Field(..., min_length=1, description="纠正后的答案")
    correction_reason: Optional[str] = Field(None, max_length=500, description="纠正原因")


class CorrectionOut(BaseModel):
    """纠正输出"""
    id: int
    message_id: int
    original_answer: str
    corrected_answer: str
    correction_reason: Optional[str]
    corrected_by: int
    status: str
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    reward_points: int
    created_at: datetime

    class Config:
        from_attributes = True


class CorrectionReview(BaseModel):
    """审核纠正"""
    status: Literal["approved", "rejected"] = Field(..., description="审核结果")
    reward_points: int = Field(0, ge=0, description="奖励积分")


# ============================================
# Question Relevance Schemas
# ============================================

class QuestionRelevanceCheck(BaseModel):
    """检查问题相关性的请求"""
    conversation_id: int = Field(..., description="当前对话ID")
    new_question: str = Field(..., min_length=1, max_length=500, description="新问题")


class QuestionRelevanceResponse(BaseModel):
    """问题相关性判断结果"""
    is_relevant: bool = Field(..., description="是否相关")
    confidence: float = Field(..., ge=0, le=1, description="置信度 0-1")
    reason: str = Field(..., max_length=100, description="判断理由")
