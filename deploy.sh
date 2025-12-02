#!/bin/bash

# Easy Book 简化部署脚本 - 北京服务器
set -e

echo "=== Easy Book 部署脚本 - 北京服务器 ==="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 停止现有容器
stop_containers() {
    log_info "停止现有容器..."
    docker stop easy-book-backend easy-book-frontend 2>/dev/null || true
    docker rm easy-book-backend easy-book-frontend 2>/dev/null || true
}

# 构建后端镜像
build_backend() {
    log_info "构建后端镜像..."
    cd backend
    docker build -t easy-book-backend .
    cd ..
}

# 构建前端镜像
build_frontend() {
    log_info "构建前端镜像..."
    cd frontend
    docker build -t easy-book-frontend .
    cd ..
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."
    docker run -d \
        --name easy-book-backend \
        --restart unless-stopped \
        -p 8002:8002 \
        -e MONGODB_URL="mongodb://easy-book:REDACTED_APP_PW@10.0.20.14:27017/easy-book" \
        -e DB_NAME="easy-book" \
        -e PYTHONPATH="/app" \
        easy-book-backend
}

# 启动前端服务
start_frontend() {
    log_info "启动前端服务..."
    docker run -d \
        --name easy-book-frontend \
        --restart unless-stopped \
        -p 8080:80 \
        easy-book-frontend
}

# 更新 Nginx 配置
configure_nginx() {
    log_info "配置 Nginx 反向代理..."

    # 备份现有配置
    sudo cp /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/default.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

    # 创建新的 Nginx 配置
    sudo tee /etc/nginx/sites-enabled/default > /dev/null << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    upstream backend {
        server localhost:8002;
    }

    upstream frontend {
        server localhost:8080;
    }

    server {
        listen 80;
        server_name _;

        # API请求代理到后端
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # 健康检查
        location /health {
            proxy_pass http://backend/health;
            proxy_set_header Host $host;
        }

        # 前端应用
        location / {
            proxy_pass http://frontend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
        }

        # 静态资源缓存
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            proxy_pass http://frontend;
            expires 1y;
            add_header Cache-Control "public, immutable";
            proxy_set_header Host $host;
        }
    }
}
EOF

    # 测试并重新加载 Nginx
    sudo nginx -t
    sudo systemctl reload nginx

    log_info "Nginx 配置已更新"
}

# 等待服务启动
wait_for_services() {
    log_info "等待服务启动..."
    sleep 20
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    # 检查后端
    if curl -f http://localhost:8002/health > /dev/null 2>&1; then
        log_info "✓ 后端服务正常 (http://localhost:8002)"
    else
        log_error "✗ 后端服务异常"
        docker logs easy-book-backend --tail 20
    fi

    # 检查前端
    if curl -f http://localhost:8080 > /dev/null 2>&1; then
        log_info "✓ 前端服务正常 (http://localhost:8080)"
    else
        log_error "✗ 前端服务异常"
        docker logs easy-book-frontend --tail 20
    fi

    # 检查完整服务
    if curl -f http://localhost > /dev/null 2>&1; then
        log_info "✓ 完整服务正常 (http://localhost)"
    else
        log_error "✗ 完整服务异常"
    fi
}

# 显示状态和访问信息
show_status() {
    log_info "容器状态:"
    docker ps -a | grep easy-book

    log_info ""
    log_info "部署完成！访问地址:"
    log_info "前端应用: http://your-server-ip/"
    log_info "后端 API: http://your-server-ip:8002/docs"
    log_info "健康检查: http://your-server-ip:8002/health"
}

# 显示日志
show_logs() {
    echo "=== 后端日志 ==="
    docker logs easy-book-backend --tail 50

    echo ""
    echo "=== 前端日志 ==="
    docker logs easy-book-frontend --tail 50
}

# 主函数
main() {
    log_info "开始部署 Easy Book..."

    stop_containers
    build_backend
    build_frontend
    start_backend
    start_frontend
    wait_for_services
    configure_nginx
    health_check
    show_status

    log_info "部署完成！"
    log_info "使用 './deploy.sh logs' 查看日志"
    log_info "使用 './deploy.sh stop' 停止服务"
    log_info "使用 './deploy.sh restart' 重启服务"
}

# 处理命令行参数
case "${1:-}" in
    "logs")
        show_logs
        ;;
    "stop")
        log_info "停止服务..."
        docker stop easy-book-backend easy-book-frontend 2>/dev/null || true
        ;;
    "restart")
        log_info "重启服务..."
        docker restart easy-book-backend easy-book-frontend 2>/dev/null || true
        ;;
    "status")
        docker ps -a | grep easy-book
        ;;
    "health")
        health_check
        ;;
    *)
        main
        ;;
esac