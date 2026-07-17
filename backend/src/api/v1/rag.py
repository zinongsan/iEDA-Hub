"""
RAG相关的API路由
提供AI问答和讲义生成接口 - 支持数据库存储
"""
from fastapi import APIRouter, HTTPException, status, Request, Depends, Body
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db, CurrentUser
from ...models.action_log import ActionLog
from ...services.conversation_service import ConversationService
from ...services.question_normalizer import QuestionNormalizer
from ...schemas.qa import (
    MessageCreate, QAResponse, ConversationOut, ConversationListResponse,
    ConversationDetailResponse, MessageOut, RatingCreate, RatingOut,
    CorrectionCreate, CorrectionOut, CorrectionReview,
    QuestionRelevanceCheck, QuestionRelevanceResponse
)

# 延迟导入RAG服务（避免启动时加载）
_rag_service = None

def get_rag_service():
    """获取RAG服务单例"""
    global _rag_service
    if _rag_service is None:
        from ...services.rag_service import RAGService
        # 初始化RAG服务
        _rag_service = RAGService(
            knowledge_base_dir="./knowledge_base",
            retrieval_mode="auto",  # 自动选择检索方式
            embedding_type="zhipu"
        )
    return _rag_service


router = APIRouter()


# ============================================
# 请求/响应模型（旧版兼容）
# ============================================

class QARequest(BaseModel):
    """AI问答请求（旧版）"""
    question: str = Field(..., min_length=1, max_length=500, description="用户问题")
    max_tokens: int = Field(500, ge=50, le=2000, description="最大输出token数")
    temperature: float = Field(0.7, ge=0, le=1, description="生成温度")


class LectureRequest(BaseModel):
    """讲义生成请求"""
    topic: str = Field(..., min_length=1, max_length=200, description="讲义主题")
    detail_level: Literal["simple", "medium", "detailed"] = Field(
        "medium",
        description="详细程度：simple简明/medium中等/detailed详细"
    )


class LectureResponse(BaseModel):
    """讲义生成响应"""
    title: str = Field(..., description="讲义标题")
    content: str = Field(..., description="讲义内容（Markdown格式）")
    sources: list[str] = Field(..., description="参考来源")
    tokens: dict = Field(..., description="token统计")
    cost: float = Field(..., description="成本（人民币）")


# ============================================
# API端点 - 对话管理
# ============================================

@router.post("/ask", response_model=QAResponse, summary="AI问答（支持对话存储）")
async def ask_question(
    request: MessageCreate,
    current: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    AI问答接口 - 新版（支持对话历史存储）

    **功能**：
    - 保存对话到数据库
    - 支持多轮对话（session_id关联）
    - 支持追问（is_followup + parent_message_id）
    - 自动记录token消耗和成本

    **示例请求**：
    ```json
    {
      "question": "什么是EDA工具？",
      "session_id": "uuid-xxx",
      "is_followup": false,
      "max_tokens": 500,
      "temperature": 0.7
    }
    ```
    """
    start_time = datetime.now()

    try:
        # 1. 获取或创建对话会话
        conv_service = ConversationService(db)
        conversation = await conv_service.get_or_create_conversation(
            user_id=current.id,
            session_id=request.session_id,
            title=request.question[:50] if len(request.question) <= 50 else request.question[:47] + "..."
        )

        # 2. ✅ 问题标准化（新增）
        normalizer = QuestionNormalizer()
        normalized = normalizer.normalize_question(request.question)

        # 3. 保存用户消息（带标准化标签）
        user_message = await conv_service.add_message(
            conversation_id=conversation.id,
            message_role="user",
            message_content=request.question,
            is_followup=request.is_followup,
            parent_message_id=request.parent_message_id,
            knowledge_tags=[normalized["normalized_topic"]] if normalized["normalized_topic"] != "unknown" else None,
            sources={
                "normalized_data": normalized,
                "question_type": normalized["question_type"],
                "keywords": normalized["keywords"]
            }
        )

        # 4. 调用RAG服务生成答案
        rag = get_rag_service()
        result = rag.generate_answer(
            question=request.question,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        # 5. 计算耗时
        elapsed_time = (datetime.now() - start_time).total_seconds() * 1000  # 毫秒

        # 6. 保存AI回答
        ai_message = await conv_service.add_message(
            conversation_id=conversation.id,
            message_role="assistant",
            message_content=result["answer"],
            sources={"sources": result.get("sources", [])},
            tokens_input=result["tokens"].get("input"),
            tokens_output=result["tokens"].get("output"),
            tokens_total=result["tokens"].get("total"),
            cost_yuan=str(result["cost"]),
            response_time_ms=int(elapsed_time),
            retrieval_mode=result.get("retrieval_mode")
        )

        # 6. 记录操作日志（action_logs表）
        try:
            log = ActionLog(
                user_id=current.id,
                action="ai.qa",
                resource_type="conversation",
                resource_id=str(conversation.id),
                ip_address=None,
                user_agent=None,
                details={
                    "question": request.question[:200],
                    "answer": result["answer"][:200],
                    "elapsed_time": elapsed_time,
                    "cost": result["cost"],
                    "tokens": result["tokens"],
                    "message_id": ai_message.id
                }
            )
            db.add(log)
            await db.commit()
        except Exception as log_error:
            print(f"[WARN] Failed to log AI QA: {log_error}")
            await db.rollback()

        # 7. 返回响应
        return QAResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            tokens=result["tokens"],
            cost=result["cost"],
            retrieval_mode=result.get("retrieval_mode", "unknown"),
            message_id=ai_message.id,
            conversation_id=conversation.id,
            user_message_id=user_message.id
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI问答失败: {str(e)}"
        )


@router.post("/qa", response_model=QAResponse, summary="AI问答（旧版兼容）", deprecated=True)
async def qa_legacy(
    request: QARequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    AI问答接口 - 旧版（为了向后兼容保留）

    **已废弃**：请使用 POST /ask 新接口，支持对话历史存储

    **功能**：
    - 不保存对话历史
    - 仅记录到 action_logs
    """
    start_time = datetime.now()

    try:
        rag = get_rag_service()

        result = rag.generate_answer(
            question=request.question,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        elapsed_time = (datetime.now() - start_time).total_seconds()

        # 记录日志（简化版）
        try:
            user_id = 1  # 默认匿名
            token = http_request.cookies.get("access_token")
            if token:
                try:
                    from ...core.security import decode_token
                    payload = decode_token(token)
                    user_id = int(payload.get("sub", 1))
                except:
                    pass

            log = ActionLog(
                user_id=user_id,
                action="ai.qa.legacy",
                resource_type="knowledge",
                resource_id=None,
                ip_address=http_request.client.host if http_request.client else None,
                user_agent=http_request.headers.get("user-agent"),
                details={
                    "question": request.question[:200],
                    "answer": result["answer"][:200],
                    "elapsed_time": elapsed_time,
                    "cost": result["cost"]
                }
            )
            db.add(log)
            await db.commit()
        except Exception:
            await db.rollback()

        # 旧版响应格式（缺少message_id等字段）
        return {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "tokens": result["tokens"],
            "cost": result["cost"],
            "retrieval_mode": result.get("retrieval_mode", "unknown"),
            "message_id": 0,  # 旧版无此字段
            "conversation_id": 0,
            "user_message_id": 0
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI问答失败: {str(e)}"
        )


@router.get("/conversations", response_model=ConversationListResponse, summary="获取对话列表")
async def get_conversations(
    current: CurrentUser,
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    page_size: int = 20
):
    """
    获取当前用户的对话列表

    **返回**：
    - conversations: 对话列表（按更新时间倒序）
    - total: 总数
    - page: 当前页
    - page_size: 每页数量
    """
    conv_service = ConversationService(db)
    conversations, total = await conv_service.get_conversations(
        user_id=current.id,
        page=page,
        page_size=page_size
    )

    # 统计每个对话的消息数
    conversation_outs = []
    for conv in conversations:
        count = await conv_service.get_message_count(conv.id)
        conversation_outs.append(
            ConversationOut(
                id=conv.id,
                user_id=conv.user_id,
                session_id=conv.session_id,
                conversation_title=conv.conversation_title,
                message_count=count,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
        )

    return ConversationListResponse(
        conversations=conversation_outs,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/conversations/search", summary="搜索对话和消息")
async def search_conversations(
    keyword: str,
    current: CurrentUser,
    db: AsyncSession = Depends(get_db),
    mode: str = "normal"  # normal 或 regex
) -> dict:
    """
    全文搜索对话标题和消息内容

    Args:
        keyword: 搜索关键词
        mode: 搜索模式 - "normal"(默认,模糊匹配) 或 "regex"(正则表达式)
        current: 当前用户
        db: 数据库会话

    Returns:
        dict: 匹配结果，包含对话ID、匹配类型、匹配的消息预览
    """
    from sqlalchemy import select, or_, func
    from ...models.qa_conversation import QAConversation
    from ...models.qa_message import QAMessage
    import re

    if not keyword or not keyword.strip():
        return {"results": []}

    keyword = keyword.strip()

    # 验证正则表达式（如果是regex模式）
    if mode == "regex":
        try:
            re.compile(keyword)
        except re.error as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的正则表达式: {str(e)}"
            )

    # 根据模式构建搜索条件
    if mode == "regex":
        # PostgreSQL使用 ~* 进行不区分大小写的正则匹配
        # MySQL使用 REGEXP
        # SQLite不支持原生正则，需要在Python层面过滤

        # 先获取所有对话和消息，然后在Python层面过滤
        title_stmt = select(QAConversation.id, QAConversation.conversation_title).where(
            QAConversation.user_id == current.id
        )
        title_result = await db.execute(title_stmt)
        title_rows = title_result.fetchall()

        # 使用Python的re模块进行正则匹配
        regex_pattern = re.compile(keyword, re.IGNORECASE)
        title_conv_ids = set()
        for conv_id, title in title_rows:
            if title and regex_pattern.search(title):
                title_conv_ids.add(conv_id)

        # 搜索消息内容
        message_stmt = select(
            QAMessage.conversation_id,
            QAMessage.message_content,
            QAMessage.message_role
        ).where(
            QAMessage.conversation_id.in_(
                select(QAConversation.id).where(QAConversation.user_id == current.id)
            )
        ).order_by(QAMessage.id)

        message_result = await db.execute(message_stmt)
        message_rows_all = message_result.fetchall()

        # Python正则过滤消息
        message_rows = []
        for row in message_rows_all:
            if row[1] and regex_pattern.search(row[1]):
                message_rows.append(row)
    else:
        # 普通模糊搜索
        search_pattern = f"%{keyword}%"

        # 搜索标题匹配的对话
        title_stmt = select(QAConversation.id).where(
            QAConversation.user_id == current.id,
            QAConversation.conversation_title.ilike(search_pattern)
        )
        title_result = await db.execute(title_stmt)
        title_conv_ids = set(row[0] for row in title_result.fetchall())

        # 搜索消息内容匹配的对话（获取详细信息）
        message_stmt = (
            select(QAMessage.conversation_id, QAMessage.message_content, QAMessage.message_role)
            .where(
                QAMessage.conversation_id.in_(
                    select(QAConversation.id).where(QAConversation.user_id == current.id)
                ),
                QAMessage.message_content.ilike(search_pattern)
            )
            .order_by(QAMessage.id)
        )
        message_result = await db.execute(message_stmt)
        message_rows = message_result.fetchall()

    # 组织消息匹配结果（每个对话只取第一条匹配的消息）
    message_matches = {}
    for conv_id, content, role in message_rows:
        if conv_id not in message_matches:
            # 截取消息预览（前100个字符）
            preview = content[:100] + "..." if len(content) > 100 else content
            message_matches[conv_id] = {
                "content": preview,
                "role": role
            }

    # 构建结果列表
    results = []
    all_conv_ids = title_conv_ids | set(message_matches.keys())

    for conv_id in all_conv_ids:
        result = {
            "conversation_id": conv_id,
            "match_type": "title" if conv_id in title_conv_ids else "message",
            "matched_message": message_matches.get(conv_id)
        }
        results.append(result)

    return {"results": results, "mode": mode}


@router.get("/conversations/stats", summary="获取评分统计")
async def get_rating_stats(
    current: CurrentUser,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    获取当前用户所有对话的评分统计信息

    Returns:
        dict: 包含各星级评分的数量和平均分
    """
    from sqlalchemy import select, func
    from ...models.qa_conversation import QAConversation
    from ...models.qa_message import QAMessage

    # 查询当前用户所有对话中的消息评分
    stmt = (
        select(QAMessage.user_rating, func.count(QAMessage.id))
        .where(
            QAMessage.conversation_id.in_(
                select(QAConversation.id).where(QAConversation.user_id == current.id)
            ),
            QAMessage.user_rating.isnot(None),
            QAMessage.user_rating >= 1,
            QAMessage.user_rating <= 5
        )
        .group_by(QAMessage.user_rating)
    )

    result = await db.execute(stmt)
    rows = result.fetchall()

    # 构建评分统计
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_ratings = 0
    total_rating_sum = 0

    for rating, count in rows:
        rating_counts[rating] = count
        total_ratings += count
        total_rating_sum += rating * count

    avg_rating = round(total_rating_sum / total_ratings, 1) if total_ratings > 0 else 0

    return {
        "rating_counts": rating_counts,
        "total_ratings": total_ratings,
        "avg_rating": avg_rating
    }


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse, summary="获取对话详情")
async def get_conversation_detail(
    conversation_id: int,
    current: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    获取对话的完整消息历史

    **返回**：
    - conversation: 对话信息
    - messages: 消息列表（按时间正序）
    """
    conv_service = ConversationService(db)
    conversation = await conv_service.get_conversation_with_messages(
        conversation_id=conversation_id,
        user_id=current.id
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在或无权访问"
        )

    # 统计消息数
    message_count = len(conversation.messages)

    conversation_out = ConversationOut(
        id=conversation.id,
        user_id=conversation.user_id,
        session_id=conversation.session_id,
        conversation_title=conversation.conversation_title,
        message_count=message_count,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )

    messages_out = [
        MessageOut.model_validate(msg) for msg in conversation.messages
    ]

    return ConversationDetailResponse(
        conversation=conversation_out,
        messages=messages_out
    )


@router.delete("/conversations/{conversation_id}", summary="删除对话")
async def delete_conversation(
    conversation_id: int,
    current: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    删除对话（级联删除所有消息）
    """
    conv_service = ConversationService(db)
    success = await conv_service.delete_conversation(
        conversation_id=conversation_id,
        user_id=current.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在或无权删除"
        )

    return {"message": "对话已删除"}


# ============================================
# API端点 - 评分与反馈
# ============================================

@router.post("/messages/{message_id}/rate", response_model=RatingOut, summary="对AI答案评分")
async def rate_message(
    message_id: int,
    request: RatingCreate,
    current: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    对AI答案进行评分（支持更新已有评分）

    **评分维度**：
    - overall_rating: 总体评分（必填）
    - accuracy_rating: 准确性
    - completeness_rating: 完整性
    - clarity_rating: 清晰度
    - feedback_text: 文字反馈
    """
    from sqlalchemy import select, update
    from ...models.qa_rating import QARating
    from ...models.qa_message import QAMessage

    try:
        # 检查评分是否已存在
        stmt = select(QARating).where(QARating.message_id == message_id)
        result = await db.execute(stmt)
        existing_rating = result.scalar_one_or_none()

        if existing_rating:
            # 更新已有评分
            stmt = (
                update(QARating)
                .where(QARating.message_id == message_id)
                .values(
                    overall_rating=request.overall_rating,
                    accuracy_rating=request.accuracy_rating,
                    completeness_rating=request.completeness_rating,
                    clarity_rating=request.clarity_rating,
                    feedback_text=request.feedback_text
                )
                .returning(QARating)
            )
            result = await db.execute(stmt)
            rating = result.scalar_one()
        else:
            # 创建新评分
            conv_service = ConversationService(db)
            rating = await conv_service.add_rating(
                message_id=message_id,
                overall_rating=request.overall_rating,
                accuracy_rating=request.accuracy_rating,
                completeness_rating=request.completeness_rating,
                clarity_rating=request.clarity_rating,
                feedback_text=request.feedback_text
            )

        # 同步更新message的user_rating字段
        stmt = (
            update(QAMessage)
            .where(QAMessage.id == message_id)
            .values(user_rating=request.overall_rating)
        )
        await db.execute(stmt)
        await db.commit()

        return RatingOut.model_validate(rating)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"评分失败: {str(e)}"
        )


@router.post("/messages/{message_id}/correct", response_model=CorrectionOut, summary="纠正AI答案")
async def correct_message(
    message_id: int,
    request: CorrectionCreate,
    current: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    纠正AI错误答案（老师功能）

    **权限**：需要老师角色
    """
    # 检查是否是老师
    if current.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有老师可以纠正答案"
        )

    # 获取原始消息
    from sqlalchemy import select
    from ...models.qa_message import QAMessage

    stmt = select(QAMessage).where(QAMessage.id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message or message.message_role != "assistant":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在或不是AI回答"
        )

    conv_service = ConversationService(db)

    try:
        correction = await conv_service.add_correction(
            message_id=message_id,
            corrected_by=current.id,
            original_answer=message.message_content,
            corrected_answer=request.corrected_answer,
            correction_reason=request.correction_reason
        )
        return CorrectionOut.model_validate(correction)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"纠正失败: {str(e)}"
        )


# ============================================
# API端点 - 讲义生成（保持不变）
# ============================================

@router.post("/lectures/generate", response_model=LectureResponse, summary="生成讲义")
async def generate_lecture(request: LectureRequest):
    """
    生成讲义接口（未集成对话存储）
    """
    try:
        rag = get_rag_service()
        result = rag.generate_lecture(
            topic=request.topic,
            detail_level=request.detail_level
        )
        return LectureResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"讲义生成失败: {str(e)}"
        )


@router.get("/status", summary="RAG服务状态")
async def get_status():
    """获取RAG服务状态"""
    try:
        rag = get_rag_service()
        return {
            "status": "ok",
            "retrieval_mode": "vector" if hasattr(rag.retriever, 'vectorstore') else "keyword",
            "knowledge_base_size": len(rag.chunks),
            "chunk_size": rag.chunk_size,
            "chunk_overlap": rag.chunk_overlap
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., min_length=1, max_length=200, description="搜索查询")
    k: int = Field(3, ge=1, le=10, description="返回结果数量")


@router.post("/search", summary="搜索知识库")
async def search(request: SearchRequest):
    """搜索知识库接口（调试用）"""
    try:
        rag = get_rag_service()
        docs = rag.search(request.query, k=request.k)
        return {
            "results": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in docs
            ],
            "count": len(docs),
            "retrieval_mode": "vector" if hasattr(rag.retriever, 'vectorstore') else "keyword"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


@router.post("/check-relevance", response_model=QuestionRelevanceResponse, summary="检查问题相关性")
async def check_question_relevance(
    request: QuestionRelevanceCheck,
    current: CurrentUser,
    db: AsyncSession = Depends(get_db)
) -> QuestionRelevanceResponse:
    """
    检查新问题与当前对话是否相关

    Args:
        request: 包含conversation_id和新问题
        current: 当前用户
        db: 数据库会话

    Returns:
        QuestionRelevanceResponse: 相关性判断结果
    """
    conv_service = ConversationService(db)

    # 1. 获取对话历史
    try:
        conversation = await conv_service.get_conversation_with_messages(
            request.conversation_id,
            current.id
        )
    except Exception as e:
        # 对话不存在或无权访问，默认相关
        import traceback
        print(f"❌ 获取对话失败: {str(e)}")
        print(traceback.format_exc())
        return QuestionRelevanceResponse(
            is_relevant=True,
            confidence=1.0,
            reason="首次提问"
        )

    # 检查对话是否为None
    if conversation is None:
        print(f"⚠️ 对话ID {request.conversation_id} 不存在或无权访问")
        return QuestionRelevanceResponse(
            is_relevant=True,
            confidence=1.0,
            reason="对话不存在"
        )

    print(f"✅ 获取到对话，消息数量: {len(conversation.messages) if conversation.messages else 0}")

    if not conversation.messages or len(conversation.messages) < 2:
        # 消息太少，默认相关
        return QuestionRelevanceResponse(
            is_relevant=True,
            confidence=1.0,
            reason="对话刚开始"
        )

    # 2. 提取对话历史文本（最近3轮，6条消息）
    history_text = ""
    recent_messages = conversation.messages[-6:] if len(conversation.messages) > 6 else conversation.messages

    for msg in recent_messages:
        role = "用户" if msg.message_role == "user" else "AI"
        content = msg.message_content[:200]  # 限制长度
        history_text += f"{role}: {content}\n"

    # 3. 使用LLM判断相关性
    import os
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )

    prompt = f"""你是一个对话分析助手。请判断新问题是否与对话历史相关。

对话历史：
{history_text}

新问题：{request.new_question}

判断规则：
1. 如果新问题是对历史内容的追问、深入探讨、举例说明、相关概念 → 相关
2. 如果新问题与历史话题完全不同（如从技术问题转到生活话题） → 不相关
3. 如果不确定，倾向于判断为相关

请以JSON格式回答（不要包含markdown代码块标记）：
{{"is_relevant": true, "confidence": 0.95, "reason": "是setup time的相关概念"}}
或
{{"is_relevant": false, "confidence": 0.98, "reason": "完全不同的话题"}}"""

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1
        )

        result_text = response.choices[0].message.content.strip()

        # 移除可能的markdown代码块标记
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1]
        if result_text.endswith("```"):
            result_text = result_text.rsplit("\n", 1)[0]
        result_text = result_text.strip()

        import json
        response_data = json.loads(result_text)

        return QuestionRelevanceResponse(
            is_relevant=response_data.get("is_relevant", True),
            confidence=float(response_data.get("confidence", 0.5)),
            reason=response_data.get("reason", "")
        )

    except Exception as e:
        logger.error(f"相关性判断失败: {e}")
        # 失败时默认相关，避免影响用户体验
        return QuestionRelevanceResponse(
            is_relevant=True,
            confidence=0.5,
            reason="判断服务暂时不可用"
        )


@router.delete("/messages/{message_id}", summary="删除单个消息")
async def delete_message(
    message_id: int,
    current: CurrentUser,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    删除单个消息

    Args:
        message_id: 消息ID
        current: 当前用户
        db: 数据库会话

    Returns:
        dict: 删除结果
    """
    from sqlalchemy import select, delete
    from ...models.qa_message import QAMessage
    from ...models.qa_conversation import QAConversation

    # 检查消息是否存在且属于当前用户
    stmt = select(QAMessage).where(QAMessage.id == message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="消息不存在")

    # 检查消息所属的对话是否属于当前用户
    stmt = select(QAConversation).where(
        QAConversation.id == message.conversation_id,
        QAConversation.user_id == current.id
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=403, detail="无权删除此消息")

    # 删除消息
    stmt = delete(QAMessage).where(QAMessage.id == message_id)
    await db.execute(stmt)
    await db.commit()

    return {"success": True, "message": "消息已删除"}


@router.patch("/conversations/{conversation_id}/title", summary="更新对话标题")
async def update_conversation_title(
    conversation_id: int,
    current: CurrentUser,
    title: str = Body(..., embed=True, max_length=100),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    更新对话标题

    Args:
        conversation_id: 对话ID
        title: 新标题
        current: 当前用户
        db: 数据库会话

    Returns:
        dict: 更新结果
    """
    from sqlalchemy import select, update
    from ...models.qa_conversation import QAConversation

    # 检查对话是否存在且属于当前用户
    stmt = select(QAConversation).where(
        QAConversation.id == conversation_id,
        QAConversation.user_id == current.id
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在或无权访问")

    # 更新标题
    stmt = (
        update(QAConversation)
        .where(QAConversation.id == conversation_id)
        .values(conversation_title=title.strip())
    )
    await db.execute(stmt)
    await db.commit()

    return {"success": True, "message": "标题已更新", "title": title.strip()}


@router.get("/conversations/{conversation_id}/export", summary="导出对话为HTML")
async def export_conversation(
    conversation_id: int,
    current: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    导出对话为HTML文件

    Args:
        conversation_id: 对话ID
        current: 当前用户
        db: 数据库会话

    Returns:
        HTML文件响应
    """
    from fastapi.responses import Response
    from sqlalchemy import select
    from ...models.qa_conversation import QAConversation
    from ...models.qa_message import QAMessage
    from datetime import datetime
    import html

    # 获取对话信息
    conv_service = ConversationService(db)
    conversation = await conv_service.get_conversation_with_messages(
        conversation_id=conversation_id,
        user_id=current.id
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在或无权访问")

    # 读取模板
    import os
    # rag.py在 /app/backend/src/api/v1/rag.py
    # 模板在 /app/backend/conversation_export_template.html
    # 需要回退3级: v1 -> api -> src -> backend
    template_path = os.path.join(os.path.dirname(__file__), "../../../conversation_export_template.html")
    template_path = os.path.abspath(template_path)

    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"导出模板文件未找到: {template_path}")

    # 准备数据
    title = conversation.conversation_title or "新对话"
    export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conversation_time = conversation.created_at.strftime("%Y-%m-%d %H:%M:%S")

    # 统计数据
    user_count = sum(1 for msg in conversation.messages if msg.message_role == "user")
    ai_count = sum(1 for msg in conversation.messages if msg.message_role == "assistant")
    message_count = len(conversation.messages)
    total_cost = sum(float(msg.cost_yuan or 0) for msg in conversation.messages)

    # 生成消息HTML
    messages_html = []
    for msg in conversation.messages:
        role = msg.message_role
        content = html.escape(msg.message_content).replace('\n', '<br>')

        # 格式化消息内容，识别加粗标记
        content = content.replace('**', '<strong>', 1)
        content = content.replace('**', '</strong>', 1)

        timestamp = msg.created_at.strftime("%H:%M:%S")

        if role == "user":
            username = current.username or "用户"
            msg_html = f'''
        <div class="message user">
          <div class="message-icon">👤</div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-role">{html.escape(username)}</span>
              <div class="message-meta"><span>{timestamp}</span></div>
            </div>
            <div class="message-text">
              <p>{content}</p>
            </div>
          </div>
        </div>'''
        else:  # assistant
            rating_html = ""
            if msg.user_rating:
                stars = "⭐" * msg.user_rating
                rating_html = f'<span class="rating">{stars}</span>'

            cost_html = f'<span class="cost">¥{msg.cost_yuan:.4f}</span>' if msg.cost_yuan else ""

            # 来源引用
            sources_html = ""
            if msg.sources:
                import json
                try:
                    sources_data = json.loads(msg.sources) if isinstance(msg.sources, str) else msg.sources
                    if sources_data and 'sources' in sources_data and sources_data['sources']:
                        sources_items = []
                        for src in sources_data['sources'][:5]:  # 最多显示5个来源
                            filename = html.escape(src.get('metadata', {}).get('file_name', '未知文件'))
                            page = src.get('metadata', {}).get('page_number', '')
                            page_info = f" - 第{page}页" if page else ""
                            sources_items.append(f'<div class="source-item">📄 {filename}{page_info}</div>')

                        if sources_items:
                            sources_html = f'''
            <div class="sources">
              <div class="sources-title">📚 参考来源</div>
              {"".join(sources_items)}
            </div>'''
                except:
                    pass

            msg_html = f'''
        <div class="message ai">
          <div class="message-icon">🤖</div>
          <div class="message-content">
            <div class="message-header">
              <span class="message-role">AI助手</span>
              <div class="message-meta">
                <span>{timestamp}</span>
                {rating_html}
                {cost_html}
              </div>
            </div>
            <div class="message-text">
              <p>{content}</p>
            </div>{sources_html}
          </div>
        </div>'''

        messages_html.append(msg_html)

    # 替换模板占位符
    html_content = template.replace("{{USERNAME}}", html.escape(current.username or "用户"))
    html_content = html_content.replace("{{TITLE}}", html.escape(title))
    html_content = html_content.replace("{{EXPORT_TIME}}", export_time)
    html_content = html_content.replace("{{CONVERSATION_TIME}}", conversation_time)
    html_content = html_content.replace("{{MESSAGE_COUNT}}", str(message_count))
    html_content = html_content.replace("{{USER_COUNT}}", str(user_count))
    html_content = html_content.replace("{{AI_COUNT}}", str(ai_count))
    html_content = html_content.replace("{{TOTAL_COST}}", f"{total_cost:.4f}")
    html_content = html_content.replace("{{MESSAGES}}", "\n".join(messages_html))

    # 返回HTML文件
    filename = f"conversation_{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
