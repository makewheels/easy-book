# Easy Book - 泳课学员管理系统

> 🏊‍♂️ 轻量级泳课学员管理系统，专为个人使用设计。

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
│   └── requirements.txt
├── frontend/             # Vue 3 前端 (Vite, port 5173 dev)
│   ├── src/
│   └── nginx-site.conf   # 生产 Nginx 配置
├── docs/                 # 项目文档
└── .github/workflows/    # CI/CD
```

## 🚀 快速开始

### 环境要求
- Python 3.12+
- Node.js 20+
- MongoDB 5.0+

### 本地开发

```bash
# 后端
cd backend
cp .env.example .env              # 配置环境变量
pip install -r requirements.txt
python run.py 8002

# 前端
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

### 运行测试

```bash
cd backend
pip install pytest pytest-asyncio httpx
python -m pytest tests/ -v
```

## 📋 核心功能

- 👥 学员管理（CRUD + 课包关联）
- 📦 课包管理（按次/按期计费）
- 📅 预约管理（日历视图、冲突检查）
- ✅ 签到管理（来了/没来、自动扣课时）
- 📱 移动端友好的响应式设计

## 🛠️ 技术栈

| 层 | 技术 |
|----|------|
| 后端 | FastAPI + Motor (MongoDB async) + Pydantic |
| 前端 | Vue 3 + Vite + Pinia |
| 数据库 | MongoDB 5.0 |
| 测试 | pytest + pytest-asyncio + httpx |
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