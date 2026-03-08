# Easy-Book 部署指南

> **目标读者:** 未来的 AI 和人类开发者。本文档包含完整部署信息，可以从零重建生产环境。

## 📋 架构概览

```
                    GitHub Actions (CI/CD)
                           │
                     push master
                           │
                    ┌──────▼──────┐
                    │  CI Tests   │
                    │ unit+integ  │
                    └──────┬──────┘
                           │ pass
                    ┌──────▼──────┐        内网
┌──────────┐  SSH   │  应用服务器  │  ──────────────  ┌──────────┐
│  用户浏览器 │◄─────►│  Nginx:80   │   10.0.20.14    │ 数据库服务器│
│           │  :80  │  FastAPI:8002│   :27017        │ MongoDB   │
└──────────┘       └─────────────┘                  └──────────┘
```

## 🖥️ 服务器信息

| 角色 | 实例ID | 公网IP | 内网IP | 系统 | SSH用户 |
|------|--------|--------|--------|------|---------|
| 应用服务器 | lhins-lit8a092 | 49.233.60.29 | 10.0.16.16 | Ubuntu 24.04 LTS | ubuntu |
| 数据库服务器 | lhins-hrxqte80 | 101.42.140.207 | 10.0.20.14 | CentOS 7.6 | root |

**SSH 密钥:** 腾讯云密钥 `lhkp-83wy0jzi`，名称 `qcloud_lighthouse_beijing`
**腾讯云 Region:** ap-beijing

## 📁 服务器目录结构

```
/home/ubuntu/
└── easy-book/                    # git clone from GitHub (SSH deploy key)
    ├── backend/
    │   ├── api_server/           # FastAPI 应用代码
    │   ├── run.py                # 入口脚本 (uvicorn, port 8002)
    │   ├── requirements.txt      # Python 依赖
    │   ├── .env                  # 环境变量 (不在 git 中)
    │   └── easy-book.service     # systemd 服务配置 (源文件)
    ├── frontend/
    │   ├── src/                  # Vue 3 源代码
    │   ├── dist/                 # npm run build 产物 (Nginx 托管)
    │   ├── nginx-site.conf       # Nginx 站点配置 (源文件)
    │   └── nginx.conf            # Docker 版 Nginx 配置 (不在裸金属部署中使用)
    └── .github/workflows/ci.yml  # CI/CD 工作流
```

## 🔑 密钥管理

### GitHub Secrets (仓库设置 → Secrets and variables → Actions)

| Secret | 说明 |
|--------|------|
| `SERVER_HOST` | 应用服务器公网 IP |
| `SERVER_USER` | SSH 用户名 (ubuntu) |
| `SSH_PRIVATE_KEY` | SSH 登录私钥 (qcloud_lighthouse_beijing) |
| `MONGODB_URL` | MongoDB 连接字符串 (含密码) |

### 环境变量文件 (backend/.env)

```env
MONGODB_URL=mongodb://easy-book:<password>@10.0.20.14:27017/easy_book?authSource=admin
DB_NAME=easy_book
ENVIRONMENT=production
```

密码从 GitHub Secrets 中的 `MONGODB_URL` 获取。模板见 `backend/.env.example`。

### MongoDB

- Docker 容器 `mongodb` 运行在数据库服务器上
- Root: `root` (密码在容器环境变量 `MONGO_INITDB_ROOT_PASSWORD` 中)
- 应用用户: `easy-book`，权限 `readWrite` on `easy_book`，认证库 `admin`

## 🚀 GitHub Actions 自动部署

**触发条件:** push 到 master 分支 + 所有 CI 测试通过

**部署流程:**
1. `backend-unit-tests` — Python pytest 单元测试
2. `backend-integration-tests` — Python pytest 集成测试 (带 MongoDB 服务)
3. `frontend-tests` — Vue TypeScript 检查 + 构建
4. `deploy` — 通过 SSH 连接服务器执行部署

**deploy 步骤:**
```bash
cd /home/ubuntu/easy-book
git pull origin master
cd backend && pip3 install -r requirements.txt --break-system-packages -q
cd ../frontend && npm ci --silent && npm run build
sudo systemctl restart easy-book
# 健康检查
curl -sf http://localhost:8002/health
curl -sf http://localhost/api/health
```

## 🛠️ 首次部署 (从零开始)

### 1. 数据库服务器 — 创建 MongoDB 用户

```bash
SSH_KEY="/path/to/qcloud_lighthouse_beijing"
ssh -i $SSH_KEY root@101.42.140.207 "
docker exec mongodb mongosh -u root -p <root_password> --authenticationDatabase admin --eval '
  use(\"admin\");
  db.createUser({
    user: \"easy-book\",
    pwd: \"<new_password>\",
    roles: [{role: \"readWrite\", db: \"easy_book\"}]
  });
'
"
```

### 2. 应用服务器 — 安装软件

```bash
ssh -i $SSH_KEY ubuntu@49.233.60.29 "
sudo apt-get update -qq
sudo apt-get install -y nginx
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs python3-pip
"
```

### 3. 应用服务器 — 部署代码

```bash
ssh -i $SSH_KEY ubuntu@49.233.60.29 "
# 配置 deploy key (需要先在 GitHub 仓库添加)
ssh-keygen -t ed25519 -C 'easy-book-deploy' -f ~/.ssh/easy-book-deploy -N ''
cat > ~/.ssh/config << 'EOF'
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/easy-book-deploy
  StrictHostKeyChecking no
EOF

# 克隆并构建
git clone git@github.com:makewheels/easy-book.git
cd easy-book/backend && pip3 install -r requirements.txt --break-system-packages
cd ../frontend && npm ci && npm run build
"
```

### 4. 应用服务器 — 上传环境变量

```bash
scp -i $SSH_KEY .env ubuntu@49.233.60.29:/home/ubuntu/easy-book/backend/.env
```

### 5. 应用服务器 — 配置 Nginx

```bash
ssh -i $SSH_KEY ubuntu@49.233.60.29 "
sudo cp /home/ubuntu/easy-book/frontend/nginx-site.conf /etc/nginx/sites-available/easy-book
sudo ln -sf /etc/nginx/sites-available/easy-book /etc/nginx/sites-enabled/easy-book
sudo rm -f /etc/nginx/sites-enabled/default
chmod 755 /home/ubuntu
sudo nginx -t && sudo systemctl restart nginx && sudo systemctl enable nginx
"
```

### 6. 应用服务器 — 配置 systemd

```bash
ssh -i $SSH_KEY ubuntu@49.233.60.29 "
sudo cp /home/ubuntu/easy-book/backend/easy-book.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable easy-book
sudo systemctl start easy-book
"
```

### 7. 验证

```bash
curl http://49.233.60.29/           # 前端页面 → 200
curl http://49.233.60.29/api/health # 后端 API → {"status":"healthy"}
```

## 🔧 常用运维命令

```bash
# SSH 连接
SSH_KEY="/path/to/qcloud_lighthouse_beijing"
ssh -i $SSH_KEY ubuntu@49.233.60.29

# 后端服务
sudo systemctl status easy-book    # 查看状态
sudo systemctl restart easy-book   # 重启
sudo journalctl -u easy-book -f    # 查看日志 (实时)
sudo journalctl -u easy-book -n 50 # 最近50行日志

# Nginx
sudo systemctl status nginx
sudo systemctl restart nginx
sudo nginx -t                      # 测试配置
sudo tail -f /var/log/nginx/error.log

# 手动部署 (不通过 GitHub Actions)
cd /home/ubuntu/easy-book
git pull origin master
cd backend && pip3 install -r requirements.txt --break-system-packages -q
cd ../frontend && npm ci && npm run build
sudo systemctl restart easy-book

# MongoDB (在数据库服务器上)
ssh -i $SSH_KEY root@101.42.140.207
docker exec -it mongodb mongosh -u root -p <password> --authenticationDatabase admin
```

## 🔄 回滚

```bash
# 回滚到指定 commit
cd /home/ubuntu/easy-book
git log --oneline -10               # 找到目标 commit
git checkout <commit-sha>
cd backend && pip3 install -r requirements.txt --break-system-packages -q
cd ../frontend && npm ci && npm run build
sudo systemctl restart easy-book
```

## 🛡️ 故障排查

| 问题 | 检查命令 |
|------|----------|
| 后端启动失败 | `sudo journalctl -u easy-book -n 50` |
| Nginx 502 | `curl localhost:8002/health` (后端是否在运行) |
| Nginx 403/500 | `sudo tail /var/log/nginx/error.log` (权限问题检查 `chmod 755 /home/ubuntu`) |
| MongoDB 连接失败 | 检查 `.env` 中 `MONGODB_URL` 是否正确；从应用服务器 `telnet 10.0.20.14 27017` |
| 前端白屏 | `ls /home/ubuntu/easy-book/frontend/dist/` (是否有构建产物) |
| deploy key 失效 | `ssh -T git@github.com` (在应用服务器上测试) |