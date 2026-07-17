#!/bin/bash

echo "🔧 修复 DbSession 错误并重启..."
cd /home/public/web_GUOCHUANG/app
sudo docker-compose restart api
echo "等待服务启动..."
sleep 10
echo "✅ 完成！请测试功能"
