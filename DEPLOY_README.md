# Easy-Book 自动部署脚本使用说明

## 📋 概述

`deploy.sh` 是一个全自动部署脚本，用于在服务器上部署Easy-Book应用。脚本会自动停止旧服务、备份代码、部署新代码、安装依赖、构建前端、配置Nginx并启动新服务。

## 🎯 适用场景

- **阿里云云效流水线**: 代码拉取完成后执行此脚本进行部署
- **手动部署**: 在服务器上直接运行进行快速部署
- **CI/CD集成**: 可集成到任何自动化流水线中

## 📁 目录结构要求

脚本执行前需要确保以下目录结构：

```
/home/ubuntu/
├── deploy.sh                    # 部署脚本（已上传）
├── easy-book-source/            # 代码源目录（云效拉取的代码）
│   ├── backend/
│   │   ├── api_server/
│   │   ├── requirements.txt
│   │   └── run.py
│   └── frontend/
│       ├── src/
│       ├── package.json
│       └── nginx.conf
└── backups/                     # 自动创建的备份目录
```

## 🚀 使用方法

### 1. 阿里云云效流水线配置

在云效流水线的构建阶段之后，添加以下命令：

```bash
# 确保代码已经拉取到 /home/ubuntu/easy-book-source 目录
cd /home/ubuntu
./deploy.sh
```

### 2. 手动部署

```bash
# 1. 确保代码在正确目录
ls /home/ubuntu/easy-book-source/

# 2. 运行部署脚本
cd /home/ubuntu
./deploy.sh
```

## ⚙️ 脚本功能详解

### 1. 环境检查
- 检查运行权限（禁止root用户运行）
- 验证源代码目录存在

### 2. 备份管理
- 自动备份现有应用到 `/home/ubuntu/backups/`
- 备份文件命名格式：`backend_backup_20251210_213000`
- 自动清理旧备份（保留最近5个）

### 3. 服务管理
- 停止现有Python后端进程
- 停止Nginx服务
- 等待进程完全停止

### 4. 代码部署
- 从 `/home/ubuntu/easy-book-source/` 复制代码
- 设置正确的文件权限
- 部署到 `/home/ubuntu/backend/` 和 `/home/ubuntu/frontend/`

### 5. 依赖安装
- 升级pip到最新版本
- 安装Python依赖包
- 安装可能缺失的系统依赖
- 安装npm依赖并构建前端

### 6. 服务配置
- 配置Nginx反向代理
- 设置虚拟主机配置
- 测试Nginx配置语法

### 7. 服务启动
- 启动后端服务（端口8002）
- 启动Nginx服务（端口80）
- 创建.env环境文件（如果不存在）

### 8. 健康检查
- 检查端口监听状态
- 验证API响应
- 确认服务正常运行

## 📊 部署后信息

部署成功后会显示：

- **访问地址**: http://服务器IP
- **后端日志**: `tail -f /tmp/backend.log`
- **Nginx日志**: `sudo journalctl -u nginx -f`
- **常用管理命令**

## 🔧 常用管理命令

```bash
# 查看后端进程
ps aux | grep python

# 查看Nginx状态
sudo systemctl status nginx

# 重启后端服务
cd /home/ubuntu/backend
pkill -f run.py
nohup python3 run.py 8002 > /tmp/backend.log 2>&1 &

# 重启Nginx
sudo systemctl restart nginx

# 查看部署日志
tail -f /tmp/deploy.log

# 查看后端日志
tail -f /tmp/backend.log
```

## 🛠️ 故障排查

### 1. 后端服务启动失败
```bash
# 查看详细错误日志
tail -50 /tmp/backend.log

# 检查Python依赖
cd /home/ubuntu/backend
pip3 list
```

### 2. Nginx配置错误
```bash
# 测试Nginx配置
sudo nginx -t

# 查看Nginx错误日志
sudo journalctl -u nginx --no-pager
```

### 3. 前端构建失败
```bash
# 手动重新构建
cd /home/ubuntu/frontend
rm -rf node_modules package-lock.json dist
npm install
npm run build
```

## 📝 环境变量配置

脚本会自动创建 `.env` 文件（如果不存在），默认配置：

```env
MONGODB_URL=mongodb://easy-book:REDACTED_APP_PW@10.0.20.14:27017/easy_book?authSource=admin
ENVIRONMENT=production
DEBUG=False
```

## 🔄 回滚操作

如果需要回滚到上一个版本：

```bash
cd /home/ubuntu/backups/
LATEST_BACKUP=$(ls -t | head -n 1 | grep backend_backup)
cp -r $LATEST_BACKUP ../backend

# 重启服务
cd /home/ubuntu
./deploy.sh
```

## ⚠️ 注意事项

1. **权限要求**: 使用ubuntu用户运行，不要使用root
2. **目录结构**: 确保代码在 `/home/ubuntu/easy-book-source/`
3. **网络连接**: 确保服务器可以访问npm和pip源
4. **磁盘空间**: 确保有足够的空间进行备份和构建
5. **MongoDB**: 确保MongoDB服务正常运行且可访问

## 🎉 部署成功标志

看到以下输出表示部署成功：

```
🎉 Easy-Book 部署完成!
=========================================
📋 部署信息:
   🕐 部署时间: 2025-12-10 21:30:00
   📁 项目目录: /home/ubuntu
   🌐 访问地址: http://49.233.60.29
   📝 后端日志: tail -f /tmp/backend.log
   📊 Nginx日志: sudo journalctl -u nginx -f
```

## 📞 支持

如果遇到问题，请检查：
1. `/tmp/deploy.log` - 部署脚本日志
2. `/tmp/backend.log` - 后端服务日志
3. `sudo journalctl -u nginx` - Nginx服务日志