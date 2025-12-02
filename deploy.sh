#!/bin/bash

echo "======================================="
echo "Easy Book 游泳课预约系统部署脚本"
echo "======================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装，请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

echo "开始部署..."

# 停止并删除现有容器（如果存在）
echo "清理现有容器..."
docker-compose down -v

# 拉取最新镜像
echo "拉取最新镜像..."
docker-compose pull

# 构建应用镜像
echo "构建应用镜像..."
docker-compose build --no-cache

# 启动服务
echo "启动服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

# 检查服务健康状态
echo "检查服务健康状态..."
echo "前端: http://localhost:80"
echo "后端API: http://localhost:8002"
echo "API文档: http://localhost:8002/docs"

# 测试后端健康检查
if curl -f http://localhost:8002/health &> /dev/null; then
    echo "✓ 后端服务启动成功"
else
    echo "✗ 后端服务启动失败"
    docker-compose logs backend
fi

# 测试前端
if curl -f http://localhost:80 &> /dev/null; then
    echo "✓ 前端服务启动成功"
else
    echo "✗ 前端服务启动失败"
    docker-compose logs frontend
fi

echo ""
echo "======================================="
echo "部署完成！"
echo "======================================="
echo "访问地址: http://localhost:80"
echo "API文档: http://localhost:8002/docs"
echo ""
echo "查看日志: docker-compose logs -f [服务名]"
echo "停止服务: docker-compose down"
echo "重启服务: docker-compose restart [服务名]"
echo "======================================="