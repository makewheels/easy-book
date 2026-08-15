# Easy-Book 部署指南

> **目标读者:** 未来的 AI 和人类开发者。本文档包含完整部署信息，可以从零重建生产环境。
> 2026-08-14 起部署在 services 机的 k3s 上（旧方案——49.233.60.29 裸机 + nginx——已废弃，该机器现为 Mac 出网隧道机，见 `~/workspace/infra/tencent-cloud`）。

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
                    ┌──────▼──────────────┐
                    │ runner rsync 代码    │
                    │ → SSH 跑 deploy.sh   │
                    └──────┬──────────────┘
                           │
┌──────────┐ HTTPS  ┌──────▼─────────────────────┐      内网        ┌──────────────┐
│ 用户浏览器 │◄──────►│ services 机 (101.42.94.17)  │ ───────────────► │ 数据库服务器    │
│          │ Caddy  │ Caddy :80/:443             │ 10.0.20.14:27017 │ MongoDB      │
│          │        │ k3s: backend + frontend    │                  │ (easy_book)  │
│          │        │      + agent(Chainlit)     │                  └──────────────┘
└──────────┘        └────────────────────────────┘
```

- 域名：**https://easybook.a4.fit**（Caddy 自动 Let's Encrypt 证书）
- **https://easybook.a4.fit/ai** — AI 助手聊天界面（Chainlit，工具调用链可视化）
- k3s namespace：`easy-book`（backend / frontend / agent 三组 Deployment+Service）
- 前端 nginx 容器托管 dist 静态文件，`/api/` 反代到 backend Service，`/ai` 反代到 agent Service（含 WebSocket 升级）
- 镜像无远端仓库：服务器上 docker build 后 `docker save | k3s ctr images import`

## 🖥️ 服务器信息

| 角色 | 公网IP | 内网IP | 系统 | SSH用户 |
|------|--------|--------|------|---------|
| 应用服务器 (services) | 101.42.94.17 | 10.0.16.4 | Ubuntu 24.04 | ubuntu |
| 数据库服务器 | 101.42.140.207 | 10.0.20.14 | CentOS 7.9 | root（仅腾讯云 TAT） |

**SSH 密钥:** 仓库 GitHub Secret `SSH_PRIVATE_KEY`（easy-book CI 专用 ed25519 key，公钥在 services 机 `~/.ssh/authorized_keys`）。本机手动登录可用 `~/.ssh/video_deploy_key`。
**数据库机维护:** 无 SSH，用腾讯云 TAT（参考 `~/workspace/infra/tencent-cloud/scripts/lib/tat.sh`）。

## 📁 服务器目录结构

```
/home/ubuntu/easy-book/          # CI rsync 同步（无 .git）
├── backend/                     # FastAPI 源码
├── frontend/                    # Vue 3 源码
├── agent/                       # book-agent（自然语言助手，不参与部署）
└── deploy/
    ├── backend.Dockerfile       # python:3.12-slim，依赖经 uv.lock 导出后走阿里云 PyPI 镜像
    ├── frontend.Dockerfile      # node 构建阶段（npmmirror）→ nginx:alpine 托管
    ├── frontend-nginx.conf      # 静态托管 + /api 反代 easy-book-backend:8002
    ├── deploy.sh                # 构建 → 导入 k3s → apply → rollout → 健康检查
    ├── k8s/                     # namespace / backend / frontend / agent / secret 模板
    ├── .mongodb-url             # MongoDB 连接串（chmod 600，不入 Git，deploy.sh 读取后创建 Secret）
    └── .agent-env               # agent 容器凭据：LLM key、Langfuse dev/prod key（chmod 600，不入 Git）
```

## 🔑 密钥管理

Infisical 的 `easy-book` 项目是应用配置真相源，dev/prod 分环境保存；共享 LLM key 只保存在 `common`，通过对应别名目录在运行时后加载。GitHub Actions 使用绑定仓库与 `master` 分支的 OIDC 短期身份，workflow 中提交的 identity ID 和 audience 均不是凭据。GitHub 不再需要保存业务密码或 Infisical client secret。

生产部署读取 `easy-book/prod` 与 `common/dev:/llm/easy-book`，把所需键通过 SSH 标准输入传到系统临时目录。`deploy.sh` 仅在本次执行中读取 `INFISICAL_ENV_FILE`；退出、失败或中断都会删除临时文件。迁移期的 `deploy/.mongodb-url` 与 `deploy/.agent-env` 只作兼容回退，完成流水线验证后应删除。

### k8s Secret（easy-book namespace）

`easy-book-config` 保存后端、Agent、Langfuse 和内部鉴权所需环境变量。它由流水线从 Infisical 的一次性输入重建；密码曾于 2026-08-14 轮换。

### MongoDB

- Docker 容器 `mongodb` 运行在数据库服务器上（10.0.20.14:27017）
- 应用用户: `easy-book`，权限 `readWrite` on `easy_book`，认证库 `admin`
- 创建/轮换密码（经 TAT 在数据库机执行）：
  ```js
  db.getSiblingDB('admin').updateUser('easy-book', {pwd: '<new_password>'})
  ```
  随后同步更新服务器 `deploy/.mongodb-url`、GitHub Secret 并重跑部署。

## 🚀 GitHub Actions 自动部署

**触发条件:** push 到 master 分支 + 所有 CI 测试通过

**部署流程:**
1. `backend-unit-tests` / `backend-integration-tests` / `frontend-tests`
2. `deploy`：runner 用 CI 密钥 rsync 代码到 `/home/ubuntu/easy-book/`（`--exclude .mongodb-url`，不会删掉凭据文件），然后 SSH 执行 `deploy/deploy.sh`：
   - `docker build` 后端/前端镜像（国内镜像源：PyPI→阿里云、npm→npmmirror、Docker Hub→daocloud 等加速）
   - `docker save | sudo k3s ctr -n k8s.io images import`
   - `kubectl apply` namespace/secret/backend/frontend
   - `rollout restart` + 等待就绪 + ClusterIP 健康检查（30 秒重试）

## 🛠️ 首次部署 (从零重建)

1. **数据库用户**：经 TAT 在数据库机 MongoDB 里 createUser `easy-book`（readWrite on easy_book）
2. **服务器凭据文件**：把连接串写入 services 机 `/home/ubuntu/easy-book/deploy/.mongodb-url`（chmod 600）
3. **k8s manifests / Dockerfile**：已在仓库 `deploy/` 中
4. **DNS**：阿里云 a4.fit 加 A 记录 `easybook` → 101.42.94.17
5. **Caddy**：`/opt/caddy/Caddyfile` 加站点（见下）并 `docker exec caddy-caddy-1 caddy reload --config /etc/caddy/Caddyfile`
   ```
   easybook.a4.fit {
       encode zstd gzip
       reverse_proxy <easy-book-frontend ClusterIP>:80
   }
   ```
   ClusterIP 查法：`sudo k3s kubectl get svc -n easy-book`（infra 仓库 `hosts/services/caddy/Caddyfile` 是编辑源）
6. **GitHub Secrets**：按上表配置；CI 密钥的公钥追加到 services 机 `authorized_keys`
7. push master 触发部署，或服务器上手动 `./deploy/deploy.sh`

## 🔧 常用运维命令

```bash
# SSH 连接（本机）
ssh -i ~/.ssh/video_deploy_key ubuntu@101.42.94.17

# Pod / 日志
sudo k3s kubectl get pods -n easy-book
sudo k3s kubectl logs -n easy-book deploy/easy-book-backend -f
sudo k3s kubectl describe pod -n easy-book <pod>

# 手动部署（服务器 /home/ubuntu/easy-book 下）
./deploy/deploy.sh

# Caddy
docker exec caddy-caddy-1 caddy validate --config /etc/caddy/Caddyfile
docker logs caddy-caddy-1 --tail 50
```

## 🔄 回滚

镜像只有 `:latest` 标签，回滚 = 检出旧 commit 重新部署：

```bash
git checkout <commit-sha>
# 本地 rsync 到服务器后执行 ./deploy/deploy.sh，或等 CI
```

## 🛡️ 故障排查

| 问题 | 检查命令 |
|------|----------|
| 后端 Pod 起不来 | `sudo k3s kubectl logs -n easy-book deploy/easy-book-backend`（常见：MongoDB 连接串失效） |
| 502/白屏 | `sudo k3s kubectl get pods -n easy-book`；Caddy 日志 |
| MongoDB 连接失败 | 从 services 机 `timeout 3 bash -c '</dev/tcp/10.0.20.14/27017'`；核对 deploy/.mongodb-url |
| 构建拉包慢/失败 | 服务器在国内：Dockerfile 已配阿里云 PyPI / npmmirror；Docker Hub 走 /etc/docker/daemon.json 里的镜像加速 |
| 证书问题 | `docker logs caddy-caddy-1` 看 ACME 日志；确认 DNS A 记录指向 101.42.94.17 |
