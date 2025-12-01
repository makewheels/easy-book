#!/bin/bash

# 构建后端Docker镜像
echo "构建后端镜像..."
docker build -t easy-book-backend:latest ./backend

# 构建前端Docker镜像
echo "构建前端镜像..."
docker build -t easy-book-frontend:latest ./frontend

echo "构建完成！"
echo ""
echo "运行镜像命令："
echo "后端: docker run -d -p 8002:8002 --name easy-book-backend easy-book-backend:latest"
echo "前端: docker run -d -p 80:80 --name easy-book-frontend easy-book-frontend:latest"