# Easy Book - 泳课学员管理系统

> 🏊‍♂️ 轻量级泳课学员管理系统，专为个人使用设计。支持自然语言操作（book-agent）。

## 🌐 生产环境

- **访问地址:** http://49.233.60.29/
- **CI/CD:** GitHub Actions — push master 自动测试 + 部署
- **部署文档:** [DEPLOY_README.md](./DEPLOY_README.md)

## 📖 项目结构

```
easy-book/
├── backend/              # FastAPI 后端 (Python 3.12, port 8002)
│   ├── api_server/       # 业务代码 (models, services, api)
│   ├── tests/            # pytest 测试 (unit + integration)
│   ├── pyproject.toml    # 依赖声明（uv 管理）
│   └── uv.lock           # uv 锁文件（CI/生产依赖唯一来源）
├── frontend/             # Vue 3 前端 (Vite, port 5173 dev, pnpm)
│   ├── src/
│   └── nginx-site.conf   # 生产 Nginx 配置
├── agent/                # book-agent 自然语言助手（工具层 + agent loop）
├── docs/                 # 项目文档
└── .github/workflows/    # CI/CD
```

## 🚀 快速开始

### 环境要求
- Python 3.12+（并安装 [uv](https://docs.astral.sh/uv/)）
- Node.js 20+（并安装 pnpm）
- MongoDB 5.0+

### 本地开发

敏感配置由自托管 Infisical 管理，仓库中的 `.infisical.json` 只包含非敏感项目定位。首次使用先执行 `infisical login --domain https://secrets.a4.fit`。后端只加载应用项目；Agent 再从 common 加载共享 LLM key，common 后加载，因此它是共享值的唯一真相源。

```bash
# 后端
cd backend
uv sync                           # 安装依赖
infisical run --project-config-dir .. --recursive -- uv run python run.py 8002

# 前端
cd frontend
pnpm install
pnpm run dev                      # http://localhost:5173
```

### 自然语言助手（可选）

```bash
cd agent
uv sync
infisical run --project-config-dir .. --recursive -- \
  infisical run --projectId 944d9216-7c11-4174-a39c-d0b339147a99 \
    --env dev --path /llm/easy-book -- \
    env BOOK_AGENT_ENVIRONMENT=development uv run book-agent ask "明天有什么课程？"
```

本地 Agent 验证必须显式设置 `BOOK_AGENT_ENVIRONMENT=development`，避免把测试 traces 写入生产项目。

详见 [agent/README.md](./agent/README.md)。

### 运行测试

```bash
# 后端（需本机 MongoDB）
cd backend
uv run pytest tests/ -v

# agent（后端不在线时 live 用例自动跳过）
cd ../agent
uv run pytest tests/ -v
```

## 📋 核心功能

- 👥 学员管理（CRUD + 课包关联 + 姓名/电话搜索）
- 📦 课包管理（记次/时长、财务分成 venue_share）
- 📅 预约管理（日历视图、冲突检查、课程标题自动生成）
- ✅ 签到管理（来了/没来、自动扣课时）
- 📈 统计分析（利润 = 售价 − 上交俱乐部、按月分组、课时余额预警）
- 🗣️ 自然语言操作（book-agent，20 个工具，写操作需确认）
- 📱 移动端友好的响应式设计

## 🛠️ 技术栈

| 层 | 技术 |
|----|------|
| 后端 | FastAPI + Motor (MongoDB async) + Pydantic |
| 前端 | Vue 3 + Vite + Pinia（pnpm） |
| 数据库 | MongoDB 5.0 |
| Agent | 手写 tool-use loop（OpenAI 兼容接口），requests 直连后端 |
| 测试 | pytest + pytest-asyncio + httpx（后端）；pytest（agent） |
| CI/CD | GitHub Actions → SSH 自动部署 |
| 服务器 | 腾讯云轻量 Ubuntu 24.04 + Nginx + systemd |

## 📚 文档导航

- **[部署指南](./DEPLOY_README.md)** — 生产环境部署、运维、故障排查
- **[需求分析](./docs/01-项目规划/需求分析.md)** — 项目背景和需求
- **[API 接口文档](./docs/03-技术架构/API接口文档.md)** — REST API 规范
- **[数据库设计](./docs/03-技术架构/数据库设计.md)** — MongoDB 集合设计
- **[后端架构](./docs/03-技术架构/后端架构设计.md)** — 服务层模块化设计
- **[前端设计](./docs/03-技术架构/前端设计.md)** — Vue 3 组件架构
- **[安装指南](./docs/04-部署运维/安装指南.md)** — 本地开发环境搭建
- **[MongoDB 配置](./docs/04-部署运维/MongoDB配置指南.md)** — 数据库初始化和管理
