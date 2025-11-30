#!/bin/bash
set -e

# ==============================================
# 配置项（根据实际情况调整）
# ==============================================
PACKAGE_PATH="/home/admin/easy-book/frontend/package.tgz"  # 流水线下载的前端包路径
DEPLOY_DIR="/home/admin/easy-book-frontend"  # 部署目录
PORT=80  # 前端服务端口（若80被占用，改8080等）
# 自动获取服务器上已安装的 Node 路径（无需手动指定版本）
NODE_PATH=$(dirname $(which node))
export PATH="$NODE_PATH:$PATH"  # 确保 Node 环境可用

# ==============================================
# 1. 验证 Node 环境（自动适配已安装的版本）
# ==============================================
echo "===== 检测 Node 环境 ====="
if ! command -v node &> /dev/null; then
  echo "❌ 未找到 Node.js，请检查服务器是否已安装"
  exit 1
fi
node -v  # 输出当前 Node 版本（应为 16.x.x）
npm -v   # 输出对应的 npm 版本
echo "=========================="

# ==============================================
# 2. 清理旧文件并解压新包
# ==============================================
echo "===== 解压前端包 ====="
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"
tar zxvf "$PACKAGE_PATH" -C "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# ==============================================
# 3. 安装依赖并构建
# ==============================================
echo "===== 安装依赖并构建 ====="
npm config set registry https://registry.npmmirror.com  # 国内源加速
npm install  # 安装项目依赖
npm run build  # 构建前端产物（根据项目调整命令）

# ==============================================
# 4. 安装 http-server（Node 静态服务工具）
# ==============================================
echo "===== 安装静态服务工具 ====="
npm install -g http-server  # 全局安装，用于启动静态服务

# ==============================================
# 5. 停止旧服务，启动新服务（后台运行）
# ==============================================
echo "===== 启动前端服务 ====="
# 停止之前的服务（避免端口占用）
pkill -f "http-server $DEPLOY_DIR/dist -p $PORT" || true
# 后台启动服务，指定构建产物目录（通常是 dist）
nohup http-server "$DEPLOY_DIR/dist" -p $PORT --cors &> "$DEPLOY_DIR/frontend.log" &

# 验证服务是否启动成功
sleep 3  # 等待服务启动
if netstat -tulpn | grep ":$PORT" &> /dev/null; then
  echo "✅ 前端服务启动成功！访问地址：http://服务器IP:$PORT"
else
  echo "❌ 服务启动失败，查看日志：cat $DEPLOY_DIR/frontend.log"
  exit 1
fi