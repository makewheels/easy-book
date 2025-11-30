@echo off
title Easy Book 泳课学员管理系统
color 0A

echo =====================================
echo    Easy Book 泳课学员管理系统
echo =====================================
echo.

REM 检查Python环境
echo [1/5] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.11+
    echo 下载地址: https://www.python.org
    pause
    exit /b 1
)
echo Python环境检查通过

REM 检查Node.js环境
echo [2/5] 检查Node.js环境...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js，请先安装Node.js 18+
    echo 下载地址: https://nodejs.org
    pause
    exit /b 1
)
echo Node.js环境检查通过

REM 检查MongoDB
echo [3/5] 检查MongoDB...
docker ps | findstr mongodb >nul 2>&1
if %errorlevel% neq 0 (
    echo MongoDB未运行，尝试启动Docker MongoDB...
    docker --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo 警告: 未找到Docker，请确保MongoDB在localhost:27017运行
        echo 或者安装Docker Desktop
    ) else (
        echo 启动MongoDB容器...
        docker run -d --name mongodb -p 27017:27017 mongo:6
        timeout /t 5 >nul
    )
)
echo MongoDB检查完成

REM 安装并启动后端
echo [4/5] 启动后端服务...
cd backend
echo 安装Python依赖...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo 错误: Python依赖安装失败，尝试使用国内镜像...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
)
echo 启动后端...
start /B python -m app.main
timeout /t 8 >nul

REM 安装并启动前端
echo [5/5] 启动前端服务...
cd ..\frontend
echo 安装Node.js依赖...
npm install
if %errorlevel% neq 0 (
    echo 错误: Node.js依赖安装失败，尝试使用国内镜像...
    npm config set registry https://registry.npmmirror.com/
    npm install
)
echo 启动前端...
start /B npm run dev
timeout /t 5 >nul

echo.
echo =====================================
echo          系统启动完成！
echo =====================================
echo.
echo 前端地址: http://localhost:5173
echo 后端地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 按任意键停止所有服务...
pause >nul

REM 停止服务
echo 正在停止服务...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
echo 所有服务已停止
pause