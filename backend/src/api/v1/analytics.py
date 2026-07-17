"""问题分析和统计API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...core.deps import get_db, CurrentUser


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/frequent-questions")
async def get_frequent_questions(
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = None,
    limit: int = Query(20, ge=1, le=100, description="返回结果数量"),
    min_count: int = Query(3, ge=1, description="最小出现次数"),
    days: Optional[int] = Query(None, ge=1, le=365, description="统计最近N天")
):
    """
    获取高频问题统计（基于标准化主题）

    **权限**：
    - 管理员：查看全局统计
    - 普通用户：查看个人统计

    **返回**：
    - topic: 标准化主题
    - count: 出现次数
    - examples: 不同的问法示例
    - avg_rating: 平均评分
    """

    # 构建时间过滤条件
    time_filter = ""
    if days:
        time_filter = f"AND m1.created_at > NOW() - INTERVAL '{days} days'"

    # 构建用户过滤条件
    user_filter = ""
    if current and not current.is_admin:
        user_filter = f"AND c.user_id = {current.id}"

    query = f"""
    WITH question_stats AS (
        SELECT
            m1.knowledge_tags[1] as topic,
            COUNT(*) as ask_count,
            array_agg(DISTINCT LEFT(m1.message_content, 80)) as examples,
            AVG(
                CASE
                    WHEN m2.user_rating IS NOT NULL
                    THEN m2.user_rating::float
                    ELSE NULL
                END
            ) as avg_rating,
            COUNT(DISTINCT c.user_id) as user_count
        FROM qa_messages m1
        JOIN qa_conversations c ON c.id = m1.conversation_id
        LEFT JOIN qa_messages m2
            ON m2.conversation_id = m1.conversation_id
            AND m2.id = m1.id + 1
            AND m2.message_role = 'assistant'
        WHERE m1.message_role = 'user'
          AND m1.knowledge_tags IS NOT NULL
          AND array_length(m1.knowledge_tags, 1) > 0
          {time_filter}
          {user_filter}
        GROUP BY m1.knowledge_tags[1]
        HAVING COUNT(*) >= :min_count
    )
    SELECT
        topic,
        ask_count,
        examples,
        ROUND(avg_rating::numeric, 2) as avg_rating,
        user_count
    FROM question_stats
    ORDER BY ask_count DESC
    LIMIT :limit;
    """

    result = await db.execute(
        text(query),
        {"min_count": min_count, "limit": limit}
    )

    rows = result.fetchall()

    return {
        "frequent_questions": [
            {
                "topic": row.topic,
                "count": row.ask_count,
                "examples": row.examples[:5] if row.examples else [],  # 最多显示5个例子
                "avg_rating": float(row.avg_rating) if row.avg_rating else None,
                "user_count": row.user_count
            }
            for row in rows
        ],
        "total": len(rows),
        "filters": {
            "days": days,
            "min_count": min_count,
            "scope": "personal" if current and not current.is_admin else "global"
        }
    }


@router.get("/weak-topics")
async def get_weak_topics(
    db: AsyncSession = Depends(get_db),
    current: CurrentUser = None,
    limit: int = Query(10, ge=1, le=50),
    user_id: Optional[int] = Query(None, description="指定用户ID（管理员可用）")
):
    """
    获取薄弱知识点（追问多、评分低、被纠正多）

    **指标**：
    - followup_rate: 追问率（高=不理解）
    - correction_rate: 纠正率（高=答案质量差）
    - avg_rating: 平均评分（低=不满意）
    """

    # 权限检查
    target_user_id = None
    if user_id:
        if current and current.is_admin:
            target_user_id = user_id
        elif current and current.id == user_id:
            target_user_id = user_id
        else:
            target_user_id = current.id if current else None
    else:
        target_user_id = current.id if current and not current.is_admin else None

    user_filter = f"AND c.user_id = {target_user_id}" if target_user_id else ""

    query = f"""
    WITH topic_analysis AS (
        SELECT
            m.knowledge_tags[1] as topic,
            COUNT(*) as total_answers,
            SUM(CASE WHEN m.is_followup = true THEN 1 ELSE 0 END) as followup_count,
            SUM(CASE WHEN m.is_corrected = true THEN 1 ELSE 0 END) as correction_count,
            AVG(CASE WHEN m.user_rating IS NOT NULL THEN m.user_rating::float ELSE NULL END) as avg_rating
        FROM qa_messages m
        JOIN qa_conversations c ON c.id = m.conversation_id
        WHERE m.message_role = 'assistant'
          AND m.knowledge_tags IS NOT NULL
          {user_filter}
        GROUP BY m.knowledge_tags[1]
        HAVING COUNT(*) >= 3
    )
    SELECT
        topic,
        total_answers,
        followup_count,
        correction_count,
        ROUND((followup_count::float / NULLIF(total_answers, 0) * 100)::numeric, 1) as followup_rate,
        ROUND((correction_count::float / NULLIF(total_answers, 0) * 100)::numeric, 1) as correction_rate,
        ROUND(avg_rating::numeric, 2) as avg_rating,
        -- 计算综合薄弱指数（越高越薄弱）
        ROUND((
            (followup_count::float / NULLIF(total_answers, 0) * 50) +
            (correction_count::float / NULLIF(total_answers, 0) * 30) +
            CASE
                WHEN avg_rating IS NOT NULL THEN (5 - avg_rating) * 4
                ELSE 0
            END
        )::numeric, 2) as weakness_score
    FROM topic_analysis
    ORDER BY weakness_score DESC
    LIMIT :limit;
    """

    result = await db.execute(text(query), {"limit": limit})
    rows = result.fetchall()

    return {
        "weak_topics": [
            {
                "topic": row.topic,
                "total_answers": row.total_answers,
                "followup_count": row.followup_count,
                "correction_count": row.correction_count,
                "followup_rate": float(row.followup_rate) if row.followup_rate else 0,
                "correction_rate": float(row.correction_rate) if row.correction_rate else 0,
                "avg_rating": float(row.avg_rating) if row.avg_rating else None,
                "weakness_score": float(row.weakness_score)
            }
            for row in rows
        ],
        "user_id": target_user_id,
        "scope": "personal" if target_user_id else "global"
    }


@router.get("/topic-trends")
async def get_topic_trends(
    topic: str,
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, ge=7, le=365)
):
    """
    获取某个主题的趋势数据（按天统计）
    """

    query = """
    SELECT
        DATE(m.created_at) as date,
        COUNT(*) as question_count,
        AVG(CASE WHEN m.user_rating IS NOT NULL THEN m.user_rating::float ELSE NULL END) as avg_rating
    FROM qa_messages m
    WHERE m.message_role = 'user'
      AND m.knowledge_tags @> ARRAY[:topic]::varchar[]
      AND m.created_at > NOW() - INTERVAL ':days days'
    GROUP BY DATE(m.created_at)
    ORDER BY date;
    """

    result = await db.execute(
        text(query),
        {"topic": topic, "days": days}
    )

    rows = result.fetchall()

    return {
        "topic": topic,
        "trends": [
            {
                "date": str(row.date),
                "question_count": row.question_count,
                "avg_rating": float(row.avg_rating) if row.avg_rating else None
            }
            for row in rows
        ]
    }
