#!/bin/bash
set -e
# easy-book 部署脚本（CentOS 专属 + 国内镜像加速）

# ========== 配置（根据项目修改）==========
PROJECT_DIR="/home/admin/easy-book"  # 服务器项目目录
BACKEND_DIR="$PROJECT_DIR/backend"   # 后端代码目录（你的项目里的backend）
MAIN_FILE="$BACKEND_DIR/run.py"      # 后端主程序（替换为你的实际文件名，比如app.py）
LOG_FILE="$BACKEND_DIR/easy-book.log"
PYTHON_CMD="python3.12"
PIP_CMD="pip3.12"
# ========================================

# 安装后端依赖
echo "=== 安装后端依赖 ==="
cd "$BACKEND_DIR" || exit 1
$PIP_CMD config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
$PIP_CMD install -r requirements.txt  # 确保backend目录下有requirements.txt

# 重启后端服务
echo "=== 重启 easy-book 后端 ==="
pkill -f "$PYTHON_CMD $MAIN_FILE" || true
nohup $PYTHON_CMD "$MAIN_FILE" > "$LOG_FILE" 2>&1 &

# 验证启动
sleep 2
if ps -ef | grep -v grep | grep "$PYTHON_CMD $MAIN_FILE"; then
  echo "✅ easy-book 后端启动成功！日志：$LOG_FILE"
  exit 0
else
  echo "❌ 启动失败！查看日志：tail -f $LOG_FILE"
  exit 1
fi