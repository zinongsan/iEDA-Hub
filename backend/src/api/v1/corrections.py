"""答案审核后台 API"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import joinedload

from ...core.deps import AdminUser, CurrentUser, DbSession
from ...models.qa_correction import QACorrection
from ...models.qa_conversation import QAConversation
from ...models.qa_message import QAMessage
from ...models.user import User
from ...schemas.correction import (
    CorrectionCreate,
    CorrectionDetail,
    CorrectionList,
    CorrectionReview,
    CorrectionStats,
    CorrectionUpdate,
)

router = APIRouter(prefix="/corrections", tags=["corrections"])


# ---------- 创建纠正记录 ----------
@router.post("", response_model=CorrectionDetail, status_code=status.HTTP_201_CREATED)
async def create_correction(
    payload: CorrectionCreate,
    user: CurrentUser,
    db: DbSession,
) -> CorrectionDetail:
    """
    创建答案纠正记录

    - 老师/学生发现AI回答错误时，提交纠正
    - 需要提供消息ID、原始答案、纠正后的答案、纠正原因
    """
    # 检查消息是否存在
    stmt = select(QAMessage).where(QAMessage.id == payload.message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "消息不存在")

    if message.message_role != "assistant":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "只能纠正AI回答")

    # 检查是否已经纠正过
    if message.is_corrected:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "该消息已经被纠正过")

    # 创建纠正记录
    correction = QACorrection(
        message_id=payload.message_id,
        original_answer=payload.original_answer,
        corrected_answer=payload.corrected_answer,
        correction_reason=payload.correction_reason,
        corrected_by=user.id,
        status="pending",
    )
    db.add(correction)

    # 更新消息的纠正状态
    message.is_corrected = True
    message.correction_id = correction.id

    await db.commit()
    await db.refresh(correction)

    # 加载关联数据
    stmt = (
        select(QACorrection)
        .options(
            joinedload(QACorrection.message).joinedload(QAMessage.conversation),
            joinedload(QACorrection.corrector),
            joinedload(QACorrection.reviewer),
        )
        .where(QACorrection.id == correction.id)
    )
    result = await db.execute(stmt)
    correction = result.scalar_one()

    return CorrectionDetail.model_validate(correction)


# ---------- 获取待审核列表 ----------
@router.get("", response_model=CorrectionList)
async def list_corrections(
    user: CurrentUser,
    db: DbSession,
    status_filter: Optional[str] = Query(None, description="状态筛选: pending/approved/rejected"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("confidence", description="排序方式: confidence(置信度)/created_at(创建时间)"),
) -> CorrectionList:
    """
    获取答案纠正列表

    - 按置信度排序：低置信度的AI回答优先审核
    - 支持状态筛选：pending(待审)/approved(通过)/rejected(拒绝)
    - 分页查询
    """
    # 构建查询
    stmt = (
        select(QACorrection)
        .options(
            joinedload(QACorrection.message).joinedload(QAMessage.conversation),
            joinedload(QACorrection.corrector),
            joinedload(QACorrection.reviewer),
        )
    )

    # 状态筛选
    if status_filter:
        stmt = stmt.where(QACorrection.status == status_filter)

    # 计算置信度（根据多个因素）
    # 1. 是否有用户评分（低评分 = 低置信度）
    # 2. 响应时间（过快或过慢 = 低置信度）
    # 3. sources数量（无来源 = 低置信度）
    confidence_score = case(
        # 有低评分（1-2星）-> 置信度10-30
        (QAMessage.user_rating.in_([1, 2]), QAMessage.user_rating * 10),
        # 有中等评分（3星）-> 置信度50
        (QAMessage.user_rating == 3, 50),
        # 有高评分（4-5星）-> 置信度70-90
        (QAMessage.user_rating.in_([4, 5]), QAMessage.user_rating * 20 - 10),
        # 无评分但有来源 -> 置信度60
        (QAMessage.sources.isnot(None), 60),
        # 无评分无来源 -> 置信度30
        else_=30
    )

    # 排序
    if order_by == "confidence":
        # 按置信度升序（低置信度优先）
        stmt = stmt.join(QAMessage, QACorrection.message_id == QAMessage.id)
        stmt = stmt.order_by(confidence_score.asc(), QACorrection.created_at.desc())
    else:
        # 按创建时间降序
        stmt = stmt.order_by(QACorrection.created_at.desc())

    # 计算总数
    count_stmt = select(func.count()).select_from(QACorrection)
    if status_filter:
        count_stmt = count_stmt.where(QACorrection.status == status_filter)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # 分页
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    corrections = result.scalars().unique().all()

    return CorrectionList(
        total=total,
        page=page,
        page_size=page_size,
        items=[CorrectionDetail.model_validate(c) for c in corrections],
    )


# ---------- 获取纠正详情 ----------
@router.get("/{correction_id}", response_model=CorrectionDetail)
async def get_correction(
    correction_id: int,
    user: CurrentUser,
    db: DbSession,
) -> CorrectionDetail:
    """
    获取纠正详情

    - 包含完整的学生问题 + AI回答
    - 包含纠正信息和审核状态
    """
    stmt = (
        select(QACorrection)
        .options(
            joinedload(QACorrection.message).joinedload(QAMessage.conversation),
            joinedload(QACorrection.corrector),
            joinedload(QACorrection.reviewer),
        )
        .where(QACorrection.id == correction_id)
    )
    result = await db.execute(stmt)
    correction = result.scalar_one_or_none()

    if not correction:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "纠正记录不存在")

    return CorrectionDetail.model_validate(correction)


# ---------- 获取对话完整上下文 ----------
@router.get("/{correction_id}/context")
async def get_correction_context(
    correction_id: int,
    user: CurrentUser,
    db: DbSession,
) -> dict:
    """
    获取纠正记录的完整对话上下文

    - 返回整个对话的所有消息
    - 方便老师了解完整背景
    """
    # 获取纠正记录
    stmt = (
        select(QACorrection)
        .options(joinedload(QACorrection.message))
        .where(QACorrection.id == correction_id)
    )
    result = await db.execute(stmt)
    correction = result.scalar_one_or_none()

    if not correction:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "纠正记录不存在")

    conversation_id = correction.message.conversation_id

    # 获取整个对话的所有消息
    stmt = (
        select(QAMessage)
        .where(QAMessage.conversation_id == conversation_id)
        .order_by(QAMessage.created_at.asc())
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    # 获取对话信息
    stmt = select(QAConversation).where(QAConversation.id == conversation_id)
    result = await db.execute(stmt)
    conversation = result.scalar_one()

    return {
        "conversation": {
            "id": conversation.id,
            "title": conversation.conversation_title,
            "created_at": conversation.created_at.isoformat(),
        },
        "messages": [
            {
                "id": msg.id,
                "role": msg.message_role,
                "content": msg.message_content,
                "sources": msg.sources,
                "user_rating": msg.user_rating,
                "is_corrected": msg.is_corrected,
                "created_at": msg.created_at.isoformat(),
                "is_current": msg.id == correction.message_id,  # 标记当前被纠正的消息
            }
            for msg in messages
        ],
    }


# ---------- 审核纠正（管理员/老师）----------
@router.post("/{correction_id}/review", response_model=CorrectionDetail)
async def review_correction(
    correction_id: int,
    payload: CorrectionReview,
    user: CurrentUser,
    db: DbSession,
    request: Request,
) -> CorrectionDetail:
    """
    审核纠正记录

    - 管理员/老师审核纠正是否合理
    - approved: 通过，奖励积分，写入知识库
    - rejected: 拒绝，不给积分
    """
    # 检查权限（只有管理员或老师可以审核）
    if not (user.is_admin or user.role == "teacher"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "只有管理员或老师可以审核")

    # 获取纠正记录
    stmt = (
        select(QACorrection)
        .options(
            joinedload(QACorrection.message).joinedload(QAMessage.conversation),
            joinedload(QACorrection.corrector),
        )
        .where(QACorrection.id == correction_id)
    )
    result = await db.execute(stmt)
    correction = result.scalar_one_or_none()

    if not correction:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "纠正记录不存在")

    if correction.status != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "该纠正已经被审核过")

    # 更新审核状态
    correction.status = payload.status
    correction.reviewed_by = user.id
    correction.reviewed_at = datetime.utcnow()

    # 如果通过，计算积分奖励
    if payload.status == "approved":
        # 基础积分：10分
        # 质量加成：根据纠正质量和重要性
        base_points = 10
        quality_bonus = payload.quality_score if payload.quality_score else 0
        correction.reward_points = base_points + quality_bonus

        # TODO: 实际发放积分到用户账户（需要积分系统）
        # await points_service.grant_points(
        #     user_id=correction.corrected_by,
        #     points=correction.reward_points,
        #     reason=f"答案纠正审核通过 #{correction_id}"
        # )

        # TODO: 将纠正内容写入知识库（需要知识库更新接口）
        # await knowledge_base_service.update_from_correction(correction)

    await db.commit()
    await db.refresh(correction)

    # 记录审核日志
    from ...models.audit import AuditLog
    audit = AuditLog(
        actor_id=user.id,
        action="review_correction",
        target=f"correction_{correction_id}",
        detail=f"status={payload.status}, quality_score={payload.quality_score}, reason={payload.review_reason}",
        ip=request.client.host if request.client else None,
    )
    db.add(audit)
    await db.commit()

    # 重新加载数据
    stmt = (
        select(QACorrection)
        .options(
            joinedload(QACorrection.message).joinedload(QAMessage.conversation),
            joinedload(QACorrection.corrector),
            joinedload(QACorrection.reviewer),
        )
        .where(QACorrection.id == correction_id)
    )
    result = await db.execute(stmt)
    correction = result.scalar_one()

    return CorrectionDetail.model_validate(correction)


# ---------- 修改纠正内容 ----------
@router.patch("/{correction_id}", response_model=CorrectionDetail)
async def update_correction(
    correction_id: int,
    payload: CorrectionUpdate,
    user: CurrentUser,
    db: DbSession,
) -> CorrectionDetail:
    """
    修改纠正内容

    - 只有创建者可以修改
    - 只能修改待审核的记录
    """
    stmt = (
        select(QACorrection)
        .options(
            joinedload(QACorrection.message).joinedload(QAMessage.conversation),
            joinedload(QACorrection.corrector),
        )
        .where(QACorrection.id == correction_id)
    )
    result = await db.execute(stmt)
    correction = result.scalar_one_or_none()

    if not correction:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "纠正记录不存在")

    # 权限检查
    if correction.corrected_by != user.id and not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "只能修改自己提交的纠正")

    if correction.status != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "只能修改待审核的纠正")

    # 更新字段
    if payload.corrected_answer is not None:
        correction.corrected_answer = payload.corrected_answer
    if payload.correction_reason is not None:
        correction.correction_reason = payload.correction_reason

    await db.commit()
    await db.refresh(correction)

    return CorrectionDetail.model_validate(correction)


# ---------- 删除纠正记录 ----------
@router.delete("/{correction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_correction(
    correction_id: int,
    user: CurrentUser,
    db: DbSession,
) -> None:
    """
    删除纠正记录

    - 只有创建者或管理员可以删除
    - 已审核的记录不能删除
    """
    stmt = select(QACorrection).where(QACorrection.id == correction_id)
    result = await db.execute(stmt)
    correction = result.scalar_one_or_none()

    if not correction:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "纠正记录不存在")

    # 权限检查
    if correction.corrected_by != user.id and not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "只能删除自己提交的纠正")

    if correction.status != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "已审核的记录不能删除")

    # 恢复消息的纠正状态
    stmt = select(QAMessage).where(QAMessage.id == correction.message_id)
    result = await db.execute(stmt)
    message = result.scalar_one_or_none()
    if message:
        message.is_corrected = False
        message.correction_id = None

    await db.delete(correction)
    await db.commit()


# ---------- 审核进度统计 ----------
@router.get("/stats/overview", response_model=CorrectionStats)
async def get_correction_stats(
    user: CurrentUser,
    db: DbSession,
) -> CorrectionStats:
    """
    获取审核进度统计

    - 待审/已审/通过/拒绝数量
    - 今日新增纠正数
    - 平均审核时间
    """
    # 各状态数量统计
    stmt = select(
        QACorrection.status,
        func.count(QACorrection.id).label("count")
    ).group_by(QACorrection.status)
    result = await db.execute(stmt)
    status_counts = {row.status: row.count for row in result}

    pending_count = status_counts.get("pending", 0)
    approved_count = status_counts.get("approved", 0)
    rejected_count = status_counts.get("rejected", 0)
    reviewed_count = approved_count + rejected_count

    # 今日新增
    from datetime import date, timedelta
    today_start = datetime.combine(date.today(), datetime.min.time())
    stmt = select(func.count()).select_from(QACorrection).where(
        QACorrection.created_at >= today_start
    )
    result = await db.execute(stmt)
    today_count = result.scalar_one()

    # 平均审核时间（已审核的记录）
    stmt = select(
        func.avg(
            func.extract('epoch', QACorrection.reviewed_at - QACorrection.created_at)
        ).label("avg_seconds")
    ).where(QACorrection.reviewed_at.isnot(None))
    result = await db.execute(stmt)
    avg_seconds = result.scalar_one()
    avg_review_hours = round(avg_seconds / 3600, 1) if avg_seconds else 0

    # 总纠正数
    stmt = select(func.count()).select_from(QACorrection)
    result = await db.execute(stmt)
    total_count = result.scalar_one()

    return CorrectionStats(
        total=total_count,
        pending=pending_count,
        approved=approved_count,
        rejected=rejected_count,
        reviewed=reviewed_count,
        today_new=today_count,
        avg_review_hours=avg_review_hours,
    )
