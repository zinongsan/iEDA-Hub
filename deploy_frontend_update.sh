#!/bin/bash

# ========================================
# 前端更新 - 启用数据库存储
# ========================================

echo ""
echo "🚀 部署前端更新 - 启用数据库存储"
echo "=========================================="
echo ""

cd /home/public/web_GUOCHUANG/app

# Step 1: 重启Nginx（重新加载前端文件）
echo "1️⃣ 重启Nginx服务..."
sudo docker-compose restart nginx
echo "   等待服务启动..."
sleep 3

# Step 2: 检查服务状态
echo ""
echo "2️⃣ 检查服务状态..."
sudo docker-compose ps nginx

echo ""
echo "=========================================="
echo "✅ 部署完成"
echo "=========================================="
echo ""
echo "📝 更新内容："
echo "   1. ✅ 前端调用新API: /api/v1/rag/ask"
echo "   2. ✅ 自动生成 session_id"
echo "   3. ✅ 对话自动保存到数据库"
echo ""
echo "🧪 测试步骤："
echo "   1. 打开前端AI界面"
echo "   2. 提问任意问题"
echo "   3. 检查数据库是否有新记录："
echo ""
echo "      sudo docker-compose exec -T db psql -U postgres -d guochuang -c \\"
echo "      SELECT id, LEFT(message_content, 40) as question, knowledge_tags"
echo "      FROM qa_messages"
echo "      WHERE message_role = 'user'"
echo "      ORDER BY id DESC LIMIT 5;\\""
echo ""
