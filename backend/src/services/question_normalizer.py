"""问题标准化服务 - 用于高频问题识别"""
import re
from typing import Optional
from openai import OpenAI
import os


class QuestionNormalizer:
    """问题标准化工具"""

    def __init__(self):
        # 使用轻量级模型做标准化
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )

        # 关键词映射表（快速匹配）
        self.keyword_mapping = {
            'setup': 'setup_time',
            '建立时间': 'setup_time',
            'hold': 'hold_time',
            '保持时间': 'hold_time',
            'sdc': 'sdc_constraint',
            '约束': 'timing_constraint',
            'eda': 'eda_tools',
            '仿真': 'simulation',
            '综合': 'synthesis',
        }

    def normalize_question(self, question: str) -> dict:
        """
        标准化问题

        Args:
            question: 原始问题

        Returns:
            {
                "normalized_topic": "setup_time",  # 标准化主题
                "keywords": ["setup", "时序", "分析"],  # 关键词
                "question_type": "concept"  # 问题类型
            }
        """
        # 方法1: 关键词快速匹配（不消耗token）
        normalized = self._quick_normalize(question)
        if normalized:
            return normalized

        # 方法2: LLM提取（更准确但消耗token）
        return self._llm_normalize(question)

    def _quick_normalize(self, question: str) -> Optional[dict]:
        """快速关键词匹配"""
        question_lower = question.lower()

        # 遍历关键词映射
        for keyword, standard_topic in self.keyword_mapping.items():
            if keyword in question_lower:
                return {
                    "normalized_topic": standard_topic,
                    "keywords": [keyword],
                    "question_type": self._infer_type(question),
                    "method": "keyword"
                }

        return None

    def _llm_normalize(self, question: str) -> dict:
        """使用LLM提取标准化主题"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": """你是问题分类专家。提取问题的核心主题。

输出JSON格式：
{
  "topic": "核心主题（英文snake_case）",
  "keywords": ["关键词1", "关键词2"],
  "type": "concept/howto/troubleshoot/comparison"
}

示例：
输入："那个setup time是啥啊？"
输出：{"topic": "setup_time", "keywords": ["setup_time", "时序"], "type": "concept"}"""
                    },
                    {
                        "role": "user",
                        "content": question
                    }
                ],
                temperature=0.3,
                max_tokens=100
            )

            import json
            result = json.loads(response.choices[0].message.content)

            return {
                "normalized_topic": result.get("topic", "unknown"),
                "keywords": result.get("keywords", []),
                "question_type": result.get("type", "unknown"),
                "method": "llm"
            }

        except Exception as e:
            # 降级处理
            return {
                "normalized_topic": "unknown",
                "keywords": self._extract_keywords(question),
                "question_type": "unknown",
                "method": "fallback"
            }

    def _infer_type(self, question: str) -> str:
        """推断问题类型"""
        if any(word in question for word in ['是什么', '什么是', '概念', '定义']):
            return 'concept'
        elif any(word in question for word in ['如何', '怎么', '怎样', '步骤']):
            return 'howto'
        elif any(word in question for word in ['错误', '问题', '报错', '失败']):
            return 'troubleshoot'
        elif any(word in question for word in ['区别', '对比', '比较']):
            return 'comparison'
        else:
            return 'unknown'

    def _extract_keywords(self, question: str) -> list[str]:
        """简单的关键词提取"""
        # 去除常见停用词
        stop_words = {'的', '是', '在', '有', '和', '就', '不', '了', '我', '他',
                      '什么', '怎么', '如何', '吗', '呢', '吧', '啊', '呀'}

        # 简单分词（实际应该用jieba等）
        words = re.findall(r'[\w]+', question)
        keywords = [w for w in words if w not in stop_words and len(w) > 1]

        return keywords[:5]  # 最多5个关键词


# ============================================
# 在保存消息时使用
# ============================================

async def save_message_with_normalization(
    conversation_service,
    conversation_id: int,
    question: str
):
    """保存消息时自动标准化"""

    # 1. 标准化问题
    normalizer = QuestionNormalizer()
    normalized = normalizer.normalize_question(question)

    # 2. 保存用户消息（带标准化信息）
    user_message = await conversation_service.add_message(
        conversation_id=conversation_id,
        message_role="user",
        message_content=question,
        knowledge_tags=[normalized["normalized_topic"]],  # 标准化主题作为标签
        # 可以把详细信息存到 sources 字段
        sources={
            "normalized_topic": normalized["normalized_topic"],
            "keywords": normalized["keywords"],
            "question_type": normalized["question_type"]
        }
    )

    return user_message, normalized


# ============================================
# 高频问题统计（基于标准化主题）
# ============================================

async def get_frequent_questions(db, limit=20):
    """获取高频问题（基于标准化主题）"""

    query = """
    SELECT
        knowledge_tags[1] as normalized_topic,
        COUNT(*) as ask_count,
        array_agg(DISTINCT message_content) as variations,
        AVG(user_rating) as avg_rating
    FROM qa_messages
    WHERE message_role = 'user'
      AND knowledge_tags IS NOT NULL
      AND array_length(knowledge_tags, 1) > 0
    GROUP BY knowledge_tags[1]
    HAVING COUNT(*) > 3
    ORDER BY ask_count DESC
    LIMIT $1;
    """

    result = await db.execute(query, limit)

    return [
        {
            "topic": row.normalized_topic,
            "count": row.ask_count,
            "variations": row.variations,  # 各种问法
            "avg_rating": row.avg_rating
        }
        for row in result
    ]
