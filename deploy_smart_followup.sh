#!/bin/bash

# ========================================
# 部署功能：智能追问判断
# ========================================

echo ""
echo "🚀 部署功能：智能追问判断"
echo "=========================================="
echo ""

cd /home/public/web_GUOCHUANG/app

echo "1️⃣ 重启API服务（加载新接口）..."
sudo docker-compose restart api

echo "   等待服务启动..."
sleep 10

echo ""
echo "2️⃣ 检查API服务状态..."
sudo docker-compose ps api

echo ""
echo "=========================================="
echo "✅ 部署完成"
echo "=========================================="
echo ""
echo "📝 新增功能："
echo "   1. ✅ 后端API: /api/v1/rag/check-relevance"
echo "   2. ✅ LLM智能判断问题相关性"
echo "   3. ✅ 前端自动检查并提示用户"
echo "   4. ✅ 用户可选择继续或新建对话"
echo ""
echo "🎯 工作流程："
echo "   用户提问"
echo "     ↓"
echo "   后端LLM判断是否相关"
echo "     ↓"
echo "   不相关 → 弹出提示"
echo "     ↓"
echo "   用户选择："
echo "     • 确定 → 自动新建对话"
echo "     • 取消 → 继续当前对话"
echo ""
echo "🧪 测试步骤："
echo "   1. 硬刷新浏览器（Ctrl+Shift+R）"
echo "   2. 打开AI对话框，提问：'什么是setup time？'"
echo "   3. 等待回答后，提问：'今天天气怎么样？'"
echo "   4. 应该弹出提示框，询问是否新建对话"
echo ""
echo "💰 成本："
echo "   - 每次检查约 ¥0.0003"
echo "   - 只在对话中途提问时检查"
echo "   - 首次提问不检查"
echo ""
