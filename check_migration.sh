#!/bin/bash

# 数据库表检查和创建脚本

echo "=========================================="
echo "📋 数据库迁移诊断和修复"
echo "=========================================="
echo ""

cd /home/public/web_GUOCHUANG/app

echo "1️⃣ 检查当前迁移版本..."
sudo docker-compose exec -T api bash -c "cd /app/backend && alembic current"

echo ""
echo "2️⃣ 查看迁移历史（最后5个）..."
sudo docker-compose exec -T api bash -c "cd /app/backend && alembic history | tail -5"

echo ""
echo "3️⃣ 检查数据库中的qa_*表..."
sudo docker-compose exec -T db psql -U postgres -d guochuang -c "\dt qa_*" || echo "❌ qa_*表不存在"

echo ""
echo "4️⃣ 尝试执行迁移到head版本..."
sudo docker-compose exec -T api bash -c "cd /app/backend && alembic upgrade head"

echo ""
echo "5️⃣ 再次检查表是否创建..."
sudo docker-compose exec -T db psql -U postgres -d guochuang -c "\dt qa_*"

echo ""
echo "6️⃣ 查看qa_conversations表结构..."
sudo docker-compose exec -T db psql -U postgres -d guochuang -c "\d qa_conversations"

echo ""
echo "=========================================="
echo "✅ 检查完成"
echo "=========================================="
