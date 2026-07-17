"""对话服务 - 处理对话的CRUD操作"""
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.qa_conversation import QAConversation
from ..models.qa_message import QAMessage
from ..models.qa_rating import QARating
from ..models.qa_correction import QACorrection


class ConversationService:
    """对话服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_conversation(
        self, user_id: int, session_id: str, title: Optional[str] = None, extra_data: Optional[dict] = None
    ) -> QAConversation:
        """
        获取或创建对话会话

        Args:
            user_id: 用户ID
            session_id: 会话ID（前端生成的UUID）
            title: 对话标题
            extra_data: 扩展数据（设备信息等）

        Returns:
            QAConversation: 对话会话对象
        """
        # 查找已存在的会话
        stmt = select(QAConversation).where(
            QAConversation.user_id == user_id,
            QAConversation.session_id == session_id
        )
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation:
            # 更新 updated_at
            conversation.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(conversation)
            return conversation

        # 创建新会话
        conversation = QAConversation(
            user_id=user_id,
            session_id=session_id,
            conversation_title=title,
            extra_data=extra_data
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def get_conversations(
        self, user_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[QAConversation], int]:
        """
        获取用户的对话列表

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量

        Returns:
            tuple: (对话列表, 总数)
        """
        # 计算总数
        count_stmt = select(func.count()).select_from(QAConversation).where(
            QAConversation.user_id == user_id
        )
        result = await self.db.execute(count_stmt)
        total = result.scalar() or 0

        # 查询对话列表
        stmt = (
            select(QAConversation)
            .where(QAConversation.user_id == user_id)
            .order_by(desc(QAConversation.updated_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        conversations = result.scalars().all()

        return conversations, total

    async def get_conversation_with_messages(
        self, conversation_id: int, user_id: int
    ) -> Optional[QAConversation]:
        """
        获取对话及其所有消息

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限检查）

        Returns:
            QAConversation: 对话对象（包含消息）
        """
        stmt = (
            select(QAConversation)
            .options(selectinload(QAConversation.messages))
            .where(
                QAConversation.id == conversation_id,
                QAConversation.user_id == user_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        """
        删除对话（级联删除所有消息）

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限检查）

        Returns:
            bool: 是否删除成功
        """
        stmt = select(QAConversation).where(
            QAConversation.id == conversation_id,
            QAConversation.user_id == user_id
        )
        result = await self.db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            return False

        await self.db.delete(conversation)
        await self.db.commit()
        return True

    async def add_message(
        self,
        conversation_id: int,
        message_role: str,
        message_content: str,
        sources: Optional[dict] = None,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None,
        tokens_total: Optional[int] = None,
        cost_yuan: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        retrieval_mode: Optional[str] = None,
        knowledge_tags: Optional[list[str]] = None,
        is_followup: bool = False,
        parent_message_id: Optional[int] = None,
    ) -> QAMessage:
        """
        添加消息到对话

        Args:
            conversation_id: 对话ID
            message_role: 消息角色（'user' 或 'assistant'）
            message_content: 消息内容
            其他参数见 QAMessage 模型

        Returns:
            QAMessage: 创建的消息对象
        """
        message = QAMessage(
            conversation_id=conversation_id,
            message_role=message_role,
            message_content=message_content,
            sources=sources,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_total=tokens_total,
            cost_yuan=cost_yuan,
            response_time_ms=response_time_ms,
            retrieval_mode=retrieval_mode,
            knowledge_tags=knowledge_tags,
            is_followup=is_followup,
            parent_message_id=parent_message_id,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_message_count(self, conversation_id: int) -> int:
        """获取对话的消息数量"""
        stmt = select(func.count()).select_from(QAMessage).where(
            QAMessage.conversation_id == conversation_id
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def add_rating(
        self,
        message_id: int,
        overall_rating: int,
        accuracy_rating: Optional[int] = None,
        completeness_rating: Optional[int] = None,
        clarity_rating: Optional[int] = None,
        feedback_text: Optional[str] = None,
    ) -> QARating:
        """
        添加评分

        Args:
            message_id: 消息ID
            overall_rating: 总体评分
            其他参数见 QARating 模型

        Returns:
            QARating: 创建的评分对象
        """
        rating = QARating(
            message_id=message_id,
            overall_rating=overall_rating,
            accuracy_rating=accuracy_rating,
            completeness_rating=completeness_rating,
            clarity_rating=clarity_rating,
            feedback_text=feedback_text,
        )
        self.db.add(rating)

        # 同步更新 message 的 user_rating 字段
        stmt = select(QAMessage).where(QAMessage.id == message_id)
        result = await self.db.execute(stmt)
        message = result.scalar_one_or_none()
        if message:
            message.user_rating = overall_rating

        await self.db.commit()
        await self.db.refresh(rating)
        return rating

    async def add_correction(
        self,
        message_id: int,
        corrected_by: int,
        original_answer: str,
        corrected_answer: str,
        correction_reason: Optional[str] = None,
    ) -> QACorrection:
        """
        添加答案纠正

        Args:
            message_id: 消息ID
            corrected_by: 纠正人ID（老师）
            original_answer: 原始答案
            corrected_answer: 纠正后的答案
            correction_reason: 纠正原因

        Returns:
            QACorrection: 创建的纠正对象
        """
        correction = QACorrection(
            message_id=message_id,
            corrected_by=corrected_by,
            original_answer=original_answer,
            corrected_answer=corrected_answer,
            correction_reason=correction_reason,
        )
        self.db.add(correction)

        # 同步更新 message 的 is_corrected 字段
        stmt = select(QAMessage).where(QAMessage.id == message_id)
        result = await self.db.execute(stmt)
        message = result.scalar_one_or_none()
        if message:
            message.is_corrected = True
            message.correction_id = correction.id

        await self.db.commit()
        await self.db.refresh(correction)
        return correction

    async def review_correction(
        self, correction_id: int, reviewed_by: int, status: str, reward_points: int = 0
    ) -> Optional[QACorrection]:
        """
        审核纠正记录

        Args:
            correction_id: 纠正ID
            reviewed_by: 审核人ID
            status: 审核状态（'approved' 或 'rejected'）
            reward_points: 奖励积分

        Returns:
            QACorrection: 更新后的纠正对象
        """
        stmt = select(QACorrection).where(QACorrection.id == correction_id)
        result = await self.db.execute(stmt)
        correction = result.scalar_one_or_none()

        if not correction:
            return None

        correction.status = status
        correction.reviewed_by = reviewed_by
        correction.reviewed_at = datetime.utcnow()
        correction.reward_points = reward_points

        await self.db.commit()
        await self.db.refresh(correction)
        return correction
