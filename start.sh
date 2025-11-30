#!/bin/bash

echo "启动 Easy Book 泳课学员管理系统..."

# 检查MongoDB是否运行
if ! pgrep -x "mongod" > /dev/null; then
    echo "启动 MongoDB..."
    docker run -d --name mongodb -p 27017:27017 mongo:6
    sleep 5
fi

# 启动后端
echo "启动后端服务..."
cd backend
pip install -r requirements.txt > /dev/null 2>&1
python -m app.main &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 启动前端
echo "启动前端服务..."
cd ../frontend
npm install > /dev/null 2>&1
npm run dev &
FRONTEND_PID=$!

echo ""
echo "系统启动完成！"
echo "前端地址: http://localhost:5173"
echo "后端地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"

# 等待用户中断
trap "echo '停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait