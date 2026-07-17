"""日志查询API"""
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import desc, select, func
from sqlalchemy.orm import joinedload

from ...core.deps import CurrentUser, DbSession
from ...models.action_log import ActionLog
from ...models.user import User
from ...schemas.log import ActionLogOut, ActionLogListResponse

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/me", response_model=ActionLogListResponse)
async def get_my_logs(
    current: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    action: str | None = Query(None, description="筛选操作类型"),
    days: int | None = Query(None, ge=1, le=90, description="最近N天"),
) -> ActionLogListResponse:
    """
    查询当前用户的操作日志

    - 只能查看自己的日志
    - 支持按操作类型筛选
    - 支持按时间范围筛选
    """
    # 构建查询
    query = select(ActionLog).where(ActionLog.user_id == current.id)

    # 筛选操作类型
    if action:
        query = query.where(ActionLog.action == action)

    # 筛选时间范围
    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.where(ActionLog.created_at >= start_date)

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar() or 0

    # 分页查询
    query = query.order_by(desc(ActionLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    # 转换为输出格式
    items = [
        ActionLogOut(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            details=log.details,
            created_at=log.created_at,
            username=current.username,
            email=current.email,
        )
        for log in logs
    ]

    return ActionLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get("/admin", response_model=ActionLogListResponse)
async def get_all_logs(
    current: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: int | None = Query(None, description="筛选用户ID"),
    action: str | None = Query(None, description="筛选操作类型"),
    days: int | None = Query(None, ge=1, le=90, description="最近N天"),
) -> ActionLogListResponse:
    """
    管理员查询所有操作日志

    - 需要管理员权限
    - 支持按用户ID筛选
    - 支持按操作类型筛选
    - 支持按时间范围筛选
    """
    # 检查管理员权限
    if not current.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要管理员权限")

    # 构建查询，关联用户信息
    query = select(ActionLog).options(joinedload(ActionLog.user))

    # 筛选用户
    if user_id:
        query = query.where(ActionLog.user_id == user_id)

    # 筛选操作类型
    if action:
        query = query.where(ActionLog.action == action)

    # 筛选时间范围
    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        query = query.where(ActionLog.created_at >= start_date)

    # 计算总数
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar() or 0

    # 分页查询
    query = query.order_by(desc(ActionLog.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    # 转换为输出格式
    items = [
        ActionLogOut(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            details=log.details,
            created_at=log.created_at,
            username=log.user.username if log.user else None,
            email=log.user.email if log.user else None,
        )
        for log in logs
    ]

    return ActionLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.get("/stats", response_model=dict)
async def get_log_stats(
    current: CurrentUser,
    db: DbSession,
    days: int = Query(7, ge=1, le=90, description="统计最近N天"),
) -> dict:
    """
    获取日志统计信息

    - 管理员：查看所有用户统计
    - 普通用户：只查看自己的统计
    """
    # 时间范围
    start_date = datetime.utcnow() - timedelta(days=days)

    # 构建查询
    if current.is_admin:
        # 管理员看所有
        query = select(
            ActionLog.action,
            func.count(ActionLog.id).label("count")
        ).where(ActionLog.created_at >= start_date)
    else:
        # 普通用户只看自己
        query = select(
            ActionLog.action,
            func.count(ActionLog.id).label("count")
        ).where(
            ActionLog.user_id == current.id,
            ActionLog.created_at >= start_date
        )

    query = query.group_by(ActionLog.action).order_by(desc("count"))

    result = await db.execute(query)
    stats = result.all()

    # 计算总数
    total = sum(row.count for row in stats)

    return {
        "period_days": days,
        "total_logs": total,
        "by_action": {row.action: row.count for row in stats}
    }
