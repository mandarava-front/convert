#!/bin/bash

# MP3 转换服务启动脚本

echo "🎵 启动 MP3 转换服务..."
echo "📁 确保必要目录存在..."

# 创建必要的目录
mkdir -p uploads midis wavs frames

echo "🚀 启动 FastAPI 服务器..."
echo "📱 服务将在以下地址启动:"
echo "   - API 服务: http://localhost:8000"
echo "   - API 文档: http://localhost:8000/docs"
echo "   - 交互式文档: http://localhost:8000/redoc"
echo ""
echo "⏹️  按 Ctrl+C 停止服务"
echo ""

# 启动服务
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload 