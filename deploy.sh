#!/bin/bash

# Easy-Book 自动部署脚本
# 作者: Claude
# 用途: 从已拉取代码的目录自动部署应用到生产环境

set -e  # 遇到错误立即退出

# 配置变量
PROJECT_DIR="/home/ubuntu"                              # 项目根目录
SOURCE_DIR="/home/ubuntu/easy-book-source"               # 代码源目录（云效拉取的代码）
BACKUP_DIR="/home/ubuntu/backups"                        # 备份目录
NGINX_SITES="/etc/nginx/sites-available"                 # Nginx站点配置目录
LOG_FILE="/tmp/deploy.log"                               # 部署日志
TIMESTAMP=$(date +%Y%m%d_%H%M%S)                        # 时间戳

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a $LOG_FILE
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a $LOG_FILE
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a $LOG_FILE
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a $LOG_FILE
}

# 检查是否以root权限运行
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "请不要以root用户运行此脚本，使用ubuntu用户运行"
        exit 1
    fi
}

# 创建备份目录
create_backup() {
    log_info "创建应用备份..."
    mkdir -p $BACKUP_DIR

    if [ -d "$PROJECT_DIR/backend" ]; then
        log_info "备份现有backend..."
        mv $PROJECT_DIR/backend $BACKUP_DIR/backend_backup_$TIMESTAMP
    fi

    if [ -d "$PROJECT_DIR/frontend" ]; then
        log_info "备份现有frontend..."
        mv $PROJECT_DIR/frontend $BACKUP_DIR/frontend_backup_$TIMESTAMP
    fi

    log_success "备份完成"
}

# 停止现有服务
stop_services() {
    log_info "停止现有服务..."

    # 停止Python后端进程
    pkill -f "python.*run.py" || true
    pkill -f "uvicorn" || true

    # 停止Nginx
    sudo systemctl stop nginx || true

    # 等待进程完全停止
    sleep 3

    log_success "服务已停止"
}

# 部署代码
deploy_code() {
    log_info "部署新代码..."

    # 检查源代码目录是否存在
    if [ ! -d "$SOURCE_DIR" ]; then
        log_error "源代码目录不存在: $SOURCE_DIR"
        log_error "请先将代码拉取到: $SOURCE_DIR"
        exit 1
    fi

    # 复制后端代码
    log_info "复制后端代码..."
    cp -r $SOURCE_DIR/backend $PROJECT_DIR/

    # 复制前端代码
    log_info "复制前端代码..."
    cp -r $SOURCE_DIR/frontend $PROJECT_DIR/

    # 设置权限
    chown -R ubuntu:ubuntu $PROJECT_DIR/backend
    chown -R ubuntu:ubuntu $PROJECT_DIR/frontend

    log_success "代码部署完成"
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."

    cd $PROJECT_DIR/backend

    # 升级pip
    python3 -m pip install --upgrade pip

    # 安装依赖
    pip3 install -r requirements.txt

    # 安装可能缺失的依赖
    pip3 install python-dateutil pymongo fastapi uvicorn python-multipart

    log_success "Python依赖安装完成"
}

# 构建前端
build_frontend() {
    log_info "构建前端..."

    cd $PROJECT_DIR/frontend

    # 安装npm依赖
    npm install

    # 构建生产版本
    npm run build

    log_success "前端构建完成"
}

# 配置Nginx
configure_nginx() {
    log_info "配置Nginx..."

    # 复制Nginx配置
    sudo cp $PROJECT_DIR/frontend/nginx.conf $NGINX_SITES/easy-book

    # 启用站点
    sudo ln -sf $NGINX_SITES/easy-book /etc/nginx/sites-enabled/easy-book

    # 删除默认站点（如果存在）
    sudo rm -f /etc/nginx/sites-enabled/default

    # 测试Nginx配置
    sudo nginx -t

    if [ $? -eq 0 ]; then
        log_success "Nginx配置正确"
    else
        log_error "Nginx配置错误"
        exit 1
    fi
}

# 启动后端服务
start_backend() {
    log_info "启动后端服务..."

    cd $PROJECT_DIR/backend

    # 确保环境变量文件存在
    if [ ! -f ".env" ]; then
        log_warning ".env文件不存在，使用默认配置"
        cat > .env << EOF
# 数据库配置
MONGODB_URL=mongodb://easy-book:REDACTED_APP_PW@10.0.20.14:27017/easy_book?authSource=admin
ENVIRONMENT=production
DEBUG=False
EOF
    fi

    # 启动后端服务
    nohup python3 run.py 8002 > /tmp/backend.log 2>&1 &

    # 等待服务启动
    sleep 5

    # 检查服务是否启动成功
    if pgrep -f "python.*run.py" > /dev/null; then
        log_success "后端服务启动成功"
    else
        log_error "后端服务启动失败，请检查日志: /tmp/backend.log"
        tail -20 /tmp/backend.log
        exit 1
    fi
}

# 启动Nginx
start_nginx() {
    log_info "启动Nginx..."

    sudo systemctl start nginx

    # 检查Nginx状态
    if sudo systemctl is-active nginx > /dev/null; then
        log_success "Nginx启动成功"
    else
        log_error "Nginx启动失败"
        sudo systemctl status nginx
        exit 1
    fi
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    # 检查后端端口
    sleep 3
    if netstat -tlnp | grep :8002 > /dev/null; then
        log_success "后端服务端口 8002 正常监听"
    else
        log_error "后端服务端口 8002 未监听"
        exit 1
    fi

    # 检查Nginx端口
    if netstat -tlnp | grep :80 > /dev/null; then
        log_success "Nginx端口 80 正常监听"
    else
        log_error "Nginx端口 80 未监听"
        exit 1
    fi

    # 检查后端API响应
    sleep 2
    if curl -s -f http://localhost:8002/docs > /dev/null; then
        log_success "后端API响应正常"
    else
        log_warning "后端API响应异常，但服务可能仍在启动中"
    fi
}

# 清理旧备份（保留最近5个）
cleanup_old_backups() {
    log_info "清理旧备份..."

    cd $BACKUP_DIR
    ls -t | grep -E "backend_backup_|frontend_backup_" | tail -n +6 | xargs rm -rf || true

    log_success "备份清理完成"
}

# 显示部署信息
show_deployment_info() {
    echo ""
    echo "========================================="
    echo "🎉 Easy-Book 部署完成!"
    echo "========================================="
    echo "📋 部署信息:"
    echo "   🕐 部署时间: $(date)"
    echo "   📁 项目目录: $PROJECT_DIR"
    echo "   🌐 访问地址: http://$(curl -s ifconfig.me)"
    echo "   📝 后端日志: tail -f /tmp/backend.log"
    echo "   📊 Nginx日志: sudo journalctl -u nginx -f"
    echo ""
    echo "🔧 常用命令:"
    echo "   查看后端进程: ps aux | grep python"
    echo "   查看Nginx状态: sudo systemctl status nginx"
    echo "   重启后端: cd $PROJECT_DIR/backend && pkill -f run.py && nohup python3 run.py 8002 > /tmp/backend.log 2>&1 &"
    echo "   重启Nginx: sudo systemctl restart nginx"
    echo "========================================="
}

# 主函数
main() {
    echo "========================================="
    echo "🚀 Easy-Book 自动部署脚本"
    echo "========================================="

    # 创建日志文件
    touch $LOG_FILE

    log_info "开始部署... $(date)"

    # 执行部署步骤
    check_root
    create_backup
    stop_services
    deploy_code
    install_python_deps
    build_frontend
    configure_nginx
    start_backend
    start_nginx
    health_check
    cleanup_old_backups
    show_deployment_info

    log_success "部署完成! $(date)"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志: $LOG_FILE"; exit 1' ERR

# 运行主函数
main "$@"