#!/bin/bash
# 重建向量数据库脚本
# 用途：应用新的chunk参数（chunk_size=500, overlap=80, k=7）

echo "=========================================="
echo "   重建iEDA-Hub向量数据库"
echo "=========================================="
echo ""

# 1. 进入项目目录
echo "步骤1：进入项目目录..."
cd ~/web_GUOCHUANG/app || { echo "错误：项目目录不存在"; exit 1; }
echo "✅ 当前目录：$(pwd)"
echo ""

# 2. 停止服务
echo "步骤2：停止API服务..."
docker-compose stop api
echo "✅ API服务已停止"
echo ""

# 3. 删除旧向量库
echo "步骤3：删除旧向量数据库..."
if [ -d "backend/chroma_db_zhipu" ]; then
    sudo rm -rf backend/chroma_db_zhipu
    echo "✅ 已删除旧向量库：backend/chroma_db_zhipu"
else
    echo "ℹ️  向量库不存在，跳过删除"
fi
echo ""

# 4. 检查知识库文件
echo "步骤4：检查知识库文件..."
file_count=$(ls backend/knowledge_base/*.txt 2>/dev/null | wc -l)
echo "📚 知识库文件数：$file_count 个"
if [ $file_count -gt 0 ]; then
    ls -lh backend/knowledge_base/*.txt
else
    echo "⚠️  警告：未找到知识库文件！"
fi
echo ""

# 5. 启动服务并重建向量库
echo "步骤5：启动API服务（自动重建向量库）..."
docker-compose start api
echo "✅ API服务已启动"
echo ""

# 6. 等待向量库重建
echo "步骤6：等待向量库重建（约90秒）..."
for i in {1..90}; do
    echo -ne "\r进度：[$i/90秒] "
    sleep 1
done
echo -e "\n✅ 等待完成"
echo ""

# 7. 查看重建日志
echo "步骤7：查看重建日志..."
echo "----------------------------------------"
docker-compose logs api | grep -E "Loading|Loaded|Splitting|Created|chunks" | tail -20
echo "----------------------------------------"
echo ""

# 8. 验证向量库是否创建成功
echo "步骤8：验证向量库..."
if [ -d "backend/chroma_db_zhipu" ]; then
    db_size=$(du -sh backend/chroma_db_zhipu | cut -f1)
    echo "✅ 向量库创建成功"
    echo "📊 向量库大小：$db_size"
    echo "📁 向量库路径：backend/chroma_db_zhipu"
else
    echo "❌ 错误：向量库创建失败！"
    echo "请查看完整日志：docker-compose logs api"
    exit 1
fi
echo ""

# 9. 测试API
echo "步骤9：测试RAG API..."
echo "测试问题：什么是EDA工具？"
response=$(curl -s -X POST http://localhost:8080/api/v1/rag/qa \
    -H "Content-Type:application/json" \
    -d'{"question":"什么是EDA工具？","max_tokens":100}' 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ API响应正常"
    echo "响应预览："
    echo "$response" | python3 -m json.tool 2>/dev/null | head -20 || echo "$response" | head -5
else
    echo "⚠️  API测试失败"
fi
echo ""

# 10. 完成
echo "=========================================="
echo "   重建完成！"
echo "=========================================="
echo ""
echo "📋 参数配置："
echo "   - chunk_size: 500"
echo "   - chunk_overlap: 80"
echo "   - 检索数量 k: 7"
echo ""
echo "🎯 下一步："
echo "   1. 在浏览器打开：http://你的服务器IP:8080/app/iedahub"
echo "   2. 点击「💬 AI智能答疑」"
echo "   3. 测试问题："
echo "      - create_clock命令怎么用？"
echo "      - SDC约束如何写？"
echo "      - 什么是静态时序分析？"
echo ""
echo "✨ 完成！"
