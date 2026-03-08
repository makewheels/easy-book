# Easy-Book 生产环境部署 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 easy-book 应用部署到腾讯云轻量服务器，配置 GitHub Actions CI/CD 自动部署流水线，清理硬编码密钥。

**Architecture:** 应用服务器 (Ubuntu 24.04, 49.233.60.29) 运行 FastAPI 后端 (systemd) + Nginx 托管前端静态文件并反代 API。数据库服务器 (CentOS 7.6, 10.0.20.14) 运行 MongoDB 5.0.5 (Docker)。GitHub Actions push master 后自动通过 SSH 部署。

**Tech Stack:** Python 3.12 / FastAPI / Motor / MongoDB 5.0.5 / Vue 3 / Vite / Nginx / systemd / GitHub Actions

---

## 服务器信息

| 角色 | 实例ID | 公网IP | 内网IP | 系统 | 用户 |
|------|--------|--------|--------|------|------|
| 应用服务器 | lhins-lit8a092 | 49.233.60.29 | 10.0.16.16 | Ubuntu 24.04 LTS | ubuntu |
| 数据库服务器 | lhins-hrxqte80 | 101.42.140.207 | 10.0.20.14 | CentOS 7.6 | root |

**SSH 密钥:** `/Users/mint/Downloads/qcloud_lighthouse_beijing` (RSA, 对应腾讯云密钥 lhkp-83wy0jzi)

**MongoDB Docker 容器:** 名称 `mongodb`, 镜像 `mongo:5.0.5`, root密码 `<ROOT_PASSWORD>`

---

### Task 1: 重置 MongoDB 用户和数据库

**目标:** 删除旧的 `easy-book` 用户和 `easy_book` 数据库数据，创建新用户。

**Step 1: 删除旧用户和数据**

```bash
SSH_KEY="/Users/mint/Downloads/qcloud_lighthouse_beijing"
SSH_OPTS="-i $SSH_KEY -o StrictHostKeyChecking=no -o PasswordAuthentication=no"

ssh $SSH_OPTS root@101.42.140.207 "
docker exec mongodb mongosh -u root -p <ROOT_PASSWORD> --authenticationDatabase admin --eval '
  use(\"admin\");
  db.dropUser(\"easy-book\");
  print(\"User easy-book dropped\");
  
  use(\"easy_book\");
  db.dropDatabase();
  print(\"Database easy_book dropped\");
'
"
```

**Step 2: 创建新用户**

生成新密码（本地执行）：
```bash
NEW_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=')
echo "New MongoDB password: $NEW_PASSWORD"
```

在 MongoDB 创建用户：
```bash
ssh $SSH_OPTS root@101.42.140.207 "
docker exec mongodb mongosh -u root -p <ROOT_PASSWORD> --authenticationDatabase admin --eval '
  use(\"admin\");
  db.createUser({
    user: \"easy-book\",
    pwd: \"$NEW_PASSWORD\",
    roles: [{role: \"readWrite\", db: \"easy_book\"}]
  });
  print(\"User easy-book created\");
'
"
```

**Step 3: 验证连接**

```bash
ssh $SSH_OPTS root@101.42.140.207 "
docker exec mongodb mongosh 'mongodb://easy-book:$NEW_PASSWORD@localhost:27017/easy_book?authSource=admin' --eval '
  db.students.insertOne({test: true});
  db.students.deleteOne({test: true});
  print(\"Connection verified!\");
'
"
```

**Step 4: 保存密码到本地 .env**

```bash
cd /Users/mint/PythonProjects/easy-book
cat > .env << EOF
# 生产环境数据库配置 - 不要提交到 git
MONGODB_URL=mongodb://easy-book:${NEW_PASSWORD}@10.0.20.14:27017/easy_book?authSource=admin
DB_NAME=easy_book
ENVIRONMENT=production
EOF
```

验证 `.env` 在 `.gitignore` 中：
```bash
grep -q "^\.env$" .gitignore && echo "OK: .env in .gitignore" || echo "ERROR: add .env to .gitignore"
```

---

### Task 2: 配置应用服务器环境

**目标:** 在应用服务器上安装 Node.js 20、Nginx、pip 依赖。

**Step 1: 安装基础软件**

```bash
ssh $SSH_OPTS ubuntu@49.233.60.29 "
# 更新系统
sudo apt-get update -qq

# 安装 Nginx
sudo apt-get install -y -qq nginx

# 安装 Node.js 20 (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y -qq nodejs

# 安装 pip
sudo apt-get install -y -qq python3-pip python3-venv

# 验证
echo '--- Versions ---'
python3 --version
node --version
npm --version
nginx -v
"
```

**Step 2: 验证安装**

Expected output:
```
Python 3.12.x
v20.x.x
10.x.x
nginx version: nginx/1.24.x
```

---

### Task 3: 部署应用代码

**目标:** 从 GitHub 克隆代码到应用服务器，安装依赖，构建前端。

**Step 1: 克隆代码并安装依赖**

```bash
ssh $SSH_OPTS ubuntu@49.233.60.29 "
# 克隆仓库
cd /home/ubuntu
git clone https://github.com/makewheels/easy-book.git

# 安装后端依赖
cd easy-book/backend
pip3 install -r requirements.txt --break-system-packages

# 安装前端依赖并构建
cd ../frontend
npm ci
npm run build

echo '--- Build output ---'
ls -la dist/
"
```

**Step 2: 创建 .env 文件**

```bash
# 从本地上传 .env 到服务器
scp $SSH_OPTS /Users/mint/PythonProjects/easy-book/.env ubuntu@49.233.60.29:/home/ubuntu/easy-book/backend/.env
```

**Step 3: 验证**

```bash
ssh $SSH_OPTS ubuntu@49.233.60.29 "
cat /home/ubuntu/easy-book/backend/.env | head -1
ls /home/ubuntu/easy-book/frontend/dist/index.html
"
```

---

### Task 4: 配置 Nginx

**目标:** 配置 Nginx 托管前端静态文件，反向代理 `/api` 到后端。

**Files:**
- Create: `frontend/nginx-site.conf` (服务器 site 配置，区别于 Docker 版 nginx.conf)

**Step 1: 创建 Nginx site 配置文件**

在本地项目中创建 `frontend/nginx-site.conf`:

```nginx
# Easy-Book Nginx Site 配置
# 部署路径: /etc/nginx/sites-available/easy-book
# 前端: /home/ubuntu/easy-book/frontend/dist
# 后端: 127.0.0.1:8002

server {
    listen 80;
    server_name _;

    root /home/ubuntu/easy-book/frontend/dist;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/javascript application/json application/xml+rss;

    # Vue Router history 模式
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理到 FastAPI 后端
    location /api/ {
        proxy_pass http://127.0.0.1:8002/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # 静态资源长缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Step 2: 上传并启用 Nginx 配置**

```bash
# 上传配置
scp $SSH_OPTS frontend/nginx-site.conf ubuntu@49.233.60.29:/tmp/easy-book

# 在服务器上启用
ssh $SSH_OPTS ubuntu@49.233.60.29 "
sudo cp /tmp/easy-book /etc/nginx/sites-available/easy-book
sudo ln -sf /etc/nginx/sites-available/easy-book /etc/nginx/sites-enabled/easy-book
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && echo 'Nginx config OK' || echo 'Nginx config ERROR'
sudo systemctl restart nginx
sudo systemctl enable nginx
"
```

**Step 3: 验证 Nginx**

```bash
ssh $SSH_OPTS ubuntu@49.233.60.29 "
curl -s -o /dev/null -w '%{http_code}' http://localhost/
"
```

Expected: `200`

---

### Task 5: 配置后端 systemd 服务

**目标:** 用 systemd 管理后端进程，开机自启，自动重启。

**Files:**
- Create: `backend/easy-book.service` (systemd unit 文件)

**Step 1: 创建 systemd service 文件**

在本地项目中创建 `backend/easy-book.service`:

```ini
# Easy-Book Backend Service
# 部署路径: /etc/systemd/system/easy-book.service
# 管理命令:
#   sudo systemctl start easy-book
#   sudo systemctl stop easy-book
#   sudo systemctl restart easy-book
#   sudo journalctl -u easy-book -f

[Unit]
Description=Easy-Book Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/easy-book/backend
EnvironmentFile=/home/ubuntu/easy-book/backend/.env
ExecStart=/usr/bin/python3 run.py 8002
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Step 2: 上传并启用服务**

```bash
scp $SSH_OPTS backend/easy-book.service ubuntu@49.233.60.29:/tmp/easy-book.service

ssh $SSH_OPTS ubuntu@49.233.60.29 "
sudo cp /tmp/easy-book.service /etc/systemd/system/easy-book.service
sudo systemctl daemon-reload
sudo systemctl enable easy-book
sudo systemctl start easy-book

# 等待启动
sleep 3
sudo systemctl status easy-book --no-pager
"
```

**Step 3: 验证后端 API**

```bash
ssh $SSH_OPTS ubuntu@49.233.60.29 "
curl -s http://localhost:8002/health | python3 -m json.tool
curl -s http://localhost/api/health | python3 -m json.tool
"
```

---

### Task 6: GitHub Actions 部署工作流

**目标:** 在 CI 通过后自动部署到生产服务器。

**Files:**
- Modify: `.github/workflows/ci.yml` — 添加 deploy job

**Step 1: 配置 GitHub Secrets**

需要在 GitHub 仓库 Settings → Secrets 中添加：
- `SERVER_HOST`: `49.233.60.29`
- `SERVER_USER`: `ubuntu`
- `SSH_PRIVATE_KEY`: SSH 私钥内容（`/Users/mint/Downloads/qcloud_lighthouse_beijing`）
- `MONGODB_URL`: MongoDB 连接字符串

使用 `gh` CLI 添加：
```bash
gh secret set SERVER_HOST --body "49.233.60.29"
gh secret set SERVER_USER --body "ubuntu"
gh secret set SSH_PRIVATE_KEY < /Users/mint/Downloads/qcloud_lighthouse_beijing
gh secret set MONGODB_URL --body "mongodb://easy-book:NEW_PASSWORD@10.0.20.14:27017/easy_book?authSource=admin"
```

**Step 2: 在 ci.yml 中添加 deploy job**

在 `ci.yml` 末尾添加：

```yaml
  deploy:
    name: 部署到生产环境
    runs-on: ubuntu-latest
    needs: [backend-unit-tests, backend-integration-tests, frontend-tests]
    if: github.ref == 'refs/heads/master' && github.event_name == 'push'

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            set -e
            cd /home/ubuntu/easy-book

            # 拉取最新代码
            git pull origin master

            # 安装后端依赖（如有变化）
            cd backend
            pip3 install -r requirements.txt --break-system-packages -q

            # 构建前端（如有变化）
            cd ../frontend
            npm ci --silent
            npm run build

            # 重启后端服务
            sudo systemctl restart easy-book

            # 等待启动并健康检查
            sleep 3
            curl -sf http://localhost:8002/health > /dev/null && echo "✅ Backend healthy" || echo "❌ Backend unhealthy"
            curl -sf http://localhost/api/health > /dev/null && echo "✅ Nginx proxy OK" || echo "❌ Nginx proxy failed"
```

**Step 3: 提交并验证**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add production deployment via SSH"
git push origin master
```

在 GitHub Actions 页面确认 deploy job 运行成功。

---

### Task 7: 清理硬编码密钥

**目标:** 从代码中移除所有硬编码的数据库密码和敏感信息。

**Files:**
- Modify: `deploy.sh:174-182` — 移除硬编码 MongoDB 密码
- Modify: `DEPLOY_README.md:163-168` — 移除硬编码连接串

**Step 1: 修改 deploy.sh**

将第 174-182 行的硬编码密码替换为环境变量引用：

```bash
# 旧代码 (deploy.sh:174-182):
    if [ ! -f ".env" ]; then
        log_warning ".env文件不存在，使用默认配置"
        cat > .env << EOF
# 数据库配置
MONGODB_URL=mongodb://easy-book:<APP_PASSWORD>@10.0.20.14:27017/easy_book?authSource=admin
ENVIRONMENT=production
DEBUG=False
EOF
    fi

# 新代码:
    if [ ! -f ".env" ]; then
        log_error ".env 文件不存在！请先创建 .env 文件配置数据库连接"
        log_error "参考: DEPLOY_README.md 中的环境变量配置"
        exit 1
    fi
```

**Step 2: 修改 DEPLOY_README.md**

将第 163-168 行替换为：

```markdown
## 📝 环境变量配置

在 `backend/.env` 文件中配置（不要提交到 git）：

```env
MONGODB_URL=mongodb://easy-book:<password>@10.0.20.14:27017/easy_book?authSource=admin
ENVIRONMENT=production
DEBUG=False
```

密码请从项目管理员获取，或查看 GitHub Secrets 中的 `MONGODB_URL`。
```

**Step 3: 提交清理**

```bash
git add deploy.sh DEPLOY_README.md
git commit -m "security: remove hardcoded MongoDB credentials"
```

---

### Task 8: 创建 .env.example

**目标:** 提供 `.env` 模板，方便未来开发者配置。

**Files:**
- Create: `backend/.env.example`

**Step 1: 创建模板文件**

```env
# Easy-Book 环境变量配置
# 复制此文件为 .env 并填入实际值
# cp .env.example .env

# MongoDB 连接字符串
# 本地开发: mongodb://localhost:27017
# 生产环境: mongodb://easy-book:<password>@10.0.20.14:27017/easy_book?authSource=admin
MONGODB_URL=mongodb://localhost:27017

# 数据库名称
DB_NAME=easy_book

# 环境标识 (development / production)
ENVIRONMENT=development
```

**Step 2: 提交**

```bash
git add backend/.env.example
git commit -m "docs: add .env.example template"
```

---

### Task 9: 更新部署文档

**目标:** 重写 DEPLOY_README.md，准确反映当前部署架构，给未来的 AI 和人类开发者看。

**Files:**
- Modify: `DEPLOY_README.md` — 全面重写

**Step 1: 重写 DEPLOY_README.md**

文档结构：
1. 架构概览（双服务器 + GitHub Actions）
2. 服务器信息表
3. 首次部署步骤（完整 step-by-step）
4. GitHub Actions 自动部署流程说明
5. 手动部署/回滚
6. MongoDB 管理（用户、备份、恢复）
7. 常用运维命令
8. 故障排查
9. Secret 管理说明

关键内容（给未来 AI 看）：
- SSH 用户是 `ubuntu`，密钥名 `qcloud_lighthouse_beijing`
- 应用部署在 `/home/ubuntu/easy-book/`
- 后端用 systemd 管理，服务名 `easy-book`
- Nginx 配置在 `/etc/nginx/sites-available/easy-book`
- MongoDB 跑在 Docker 容器 `mongodb` 里（数据库服务器上）
- MongoDB root 密码在容器环境变量里
- 应用 MongoDB 密码在 GitHub Secret `MONGODB_URL` 里
- 前端构建产物在 `frontend/dist/`

**Step 2: 提交**

```bash
git add DEPLOY_README.md
git commit -m "docs: rewrite deployment guide for current architecture"
```

---

### Task 10: 端到端验证

**目标:** 验证整个部署链路正常。

**Step 1: 验证生产环境可访问**

```bash
# 前端页面
curl -s -o /dev/null -w "%{http_code}" http://49.233.60.29/
# Expected: 200

# 后端 API (通过 Nginx)
curl -s http://49.233.60.29/api/health
# Expected: {"status": "ok"}

# 学生列表 API
curl -s http://49.233.60.29/api/students/ | python3 -m json.tool
# Expected: []  (空数组，数据库已清空)
```

**Step 2: 验证 GitHub Actions 自动部署**

```bash
# 做一个小改动测试部署流水线
echo "" >> constitution.md
git add constitution.md
git commit -m "test: verify CI/CD pipeline"
git push origin master
```

在 GitHub Actions 页面确认所有 job（包括 deploy）成功。

**Step 3: 验证部署后服务正常**

```bash
ssh $SSH_OPTS ubuntu@49.233.60.29 "
sudo systemctl status easy-book --no-pager | head -5
curl -s http://localhost:8002/health
curl -s http://localhost/api/students/
"
```

---

### Task 11: 提交所有变更并创建 PR

**Step 1: 创建 deployment 分支**

```bash
git checkout -b deployment
git add -A
git commit -m "feat: production deployment with GitHub Actions CI/CD

- Add nginx-site.conf for bare-metal Nginx
- Add easy-book.service for systemd
- Add .env.example template
- Add deploy job to CI workflow
- Remove hardcoded credentials from deploy.sh
- Rewrite DEPLOY_README.md for current architecture"
git push origin deployment
gh pr create --title "feat: 生产环境部署 + GitHub Actions CI/CD" --body "..."
```

**Step 2: 合并**

```bash
gh pr merge --squash --admin
git checkout master && git pull origin master
```

---

## 文件清单

| 操作 | 文件 | 说明 |
|------|------|------|
| Create | `frontend/nginx-site.conf` | 裸金属 Nginx site 配置 |
| Create | `backend/easy-book.service` | systemd 服务单元文件 |
| Create | `backend/.env.example` | 环境变量模板 |
| Create | `backend/.env` (本地) | 实际密钥（不提交 git） |
| Modify | `.github/workflows/ci.yml` | 添加 deploy job |
| Modify | `deploy.sh` | 移除硬编码密码 |
| Modify | `DEPLOY_README.md` | 重写部署文档 |

## GitHub Secrets 清单

| Secret | 值 | 说明 |
|--------|-----|------|
| `SERVER_HOST` | `49.233.60.29` | 应用服务器 IP |
| `SERVER_USER` | `ubuntu` | SSH 用户名 |
| `SSH_PRIVATE_KEY` | 私钥文件内容 | SSH 登录密钥 |
| `MONGODB_URL` | `mongodb://easy-book:xxx@10.0.20.14:27017/easy_book?authSource=admin` | 数据库连接 |
