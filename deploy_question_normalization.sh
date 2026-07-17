#!/bin/bash

# ========================================
# 方案1 - 问题标准化功能部署脚本
# ========================================

echo ""
echo "🚀 部署方案1 - 问题标准化功能"
echo "=========================================="
echo ""

cd /home/public/web_GUOCHUANG/app

# Step 1: 重启API服务
echo "1️⃣ 重启API服务（加载新代码）..."
sudo docker-compose restart api
echo "   等待服务启动..."
sleep 10

# Step 2: 检查服务状态
echo ""
echo "2️⃣ 检查服务状态..."
sudo docker-compose ps api

# Step 3: 测试问答接口（带问题标准化）
echo ""
echo "3️⃣ 测试问答接口（问题标准化）..."
echo "   问题: '那个setup time是啥啊？'（口语化）"
curl -s -X POST "http://localhost:8080/api/v1/rag/ask" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "question": "那个setup time是啥啊？",
    "session_id": "test-normalization-001",
    "max_tokens": 150,
    "temperature": 0.7
  }' | jq '.' || curl -s -X POST "http://localhost:8080/api/v1/rag/ask" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "question": "那个setup time是啥啊？",
    "session_id": "test-normalization-001",
    "max_tokens": 150,
    "temperature": 0.7
  }'

echo ""
echo ""
echo "4️⃣ 再发送一个不同表达的问题..."
echo "   问题: '建立时间是什么意思？'（标准问法）"
curl -s -X POST "http://localhost:8080/api/v1/rag/ask" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "question": "建立时间是什么意思？",
    "session_id": "test-normalization-001",
    "max_tokens": 150,
    "temperature": 0.7
  }' > /dev/null 2>&1

echo "   ✅ 已发送"

# Step 5: 检查数据库中的标准化标签
echo ""
echo "5️⃣ 检查数据库中的标准化结果..."
sudo docker-compose exec -T db psql -U postgres -d guochuang -c "
SELECT
    id,
    LEFT(message_content, 40) as question,
    knowledge_tags as normalized_topic,
    sources->'normalized_data'->>'question_type' as type
FROM qa_messages
WHERE message_role = 'user'
ORDER BY id DESC
LIMIT 5;
"

# Step 6: 测试高频问题统计API
echo ""
echo "6️⃣ 测试高频问题统计API..."
curl -s -X GET "http://localhost:8080/api/v1/rag/analytics/frequent-questions?limit=10&min_count=1" \
  -b cookies.txt | jq '.' || curl -s -X GET "http://localhost:8080/api/v1/rag/analytics/frequent-questions?limit=10&min_count=1" -b cookies.txt

# Step 7: 测试薄弱知识点API
echo ""
echo ""
echo "7️⃣ 测试薄弱知识点API..."
curl -s -X GET "http://localhost:8080/api/v1/rag/analytics/weak-topics?limit=5" \
  -b cookies.txt | jq '.' || curl -s -X GET "http://localhost:8080/api/v1/rag/analytics/weak-topics?limit=5" -b cookies.txt

echo ""
echo ""
echo "=========================================="
echo "✅ 部署完成"
echo "=========================================="
echo ""
echo "📊 新功能："
echo "   1. ✅ 问题自动标准化（保存时）"
echo "   2. ✅ 高频问题统计API"
echo "   3. ✅ 薄弱知识点分析API"
echo ""
echo "🔗 API接口："
echo "   GET  /api/v1/rag/analytics/frequent-questions"
echo "   GET  /api/v1/rag/analytics/weak-topics"
echo "   GET  /api/v1/rag/analytics/topic-trends?topic=xxx"
echo ""
echo "📚 下一步："
echo "   1. 多测试几个口语化问题"
echo "   2. 查看高频问题统计效果"
echo "   3. 根据实际使用调整关键词库"
echo ""
