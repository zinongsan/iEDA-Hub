#!/bin/bash

# 对话Log系统数据库迁移脚本
# 用途：执行数据库迁移，创建qa_*表

set -e

echo "=========================================="
echo "对话Log系统 - 数据库迁移"
echo "=========================================="
echo ""

# 检查当前目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误：请在项目根目录（包含docker-compose.yml）运行此脚本"
    exit 1
fi

echo "✅ 当前目录：$(pwd)"
echo ""

# 检查Docker服务状态
echo "📋 检查Docker服务状态..."
sudo docker-compose ps

echo ""
echo "🔍 检查当前迁移状态..."
sudo docker-compose exec -T api bash -c "cd /app/backend && alembic current"

echo ""
echo "📜 查看迁移历史..."
sudo docker-compose exec -T api bash -c "cd /app/backend && alembic history | tail -5"

echo ""
read -p "是否执行迁移到最新版本？(y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 开始执行数据库迁移..."
    sudo docker-compose exec -T api bash -c "cd /app/backend && alembic upgrade head"

    echo ""
    echo "✅ 迁移完成！"
    echo ""
    echo "🔍 验证迁移结果..."
    sudo docker-compose exec -T api bash -c "cd /app/backend && alembic current"

    echo ""
    echo "📊 检查新创建的表..."
    sudo docker-compose exec -T db psql -U postgres -d guochuang -c "\\dt qa_*"

    echo ""
    echo "=========================================="
    echo "✨ 数据库迁移成功完成！"
    echo "=========================================="
    echo ""
    echo "接下来的步骤："
    echo "1. 测试新API接口"
    echo "2. 前端集成新接口"
    echo "3. 迁移localStorage数据"
    echo ""
else
    echo ""
    echo "❌ 已取消迁移"
    exit 0
fi
