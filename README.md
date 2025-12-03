# Easy Book - 泳课学员管理系统

一个轻量级的泳课学员管理系统，专为个人使用设计。

## 功能特点

- 📱 移动端友好设计
- 👥 学员管理（增删改查）
- 📅 预约管理（创建、查询、冲突检查）
- ✅ 签到管理（签到、缺席、自动扣费）
- 📊 课程统计

## 技术栈

### 后端
- FastAPI (Python 3.11+)
- MongoDB
- PyMongo

### 前端
- Vue 3
- Vite
- Pinia (状态管理)
- Axios

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- MongoDB 6.0+

### 1. 启动MongoDB

```bash
# 使用Docker启动MongoDB
docker run -d --name mongodb -p 27017:27017 mongo:6

# 或使用本地MongoDB服务
mongod
```

### 2. 启动后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m app.main
```

后端服务将在 http://localhost:8000 启动

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将在 http://localhost:5173 启动

## 使用说明

### 学员管理
1. 在"学生管理"页面查看所有学员
2. 点击"+ 新增学生"添加新学员
3. 点击学员卡片查看详情
4. 在详情页面可以编辑学员信息或创建预约

### 预约管理
1. 在首页查看今日/明日预约
2. 点击"签到"或"缺席"按钮完成考勤
3. 签到会自动扣减剩余课程数
4. 在学员详情页可以创建新预约

### 课程扣费
- 签到：剩余课程数 -1
- 缺席：剩余课程数不变
- 所有扣费只在签到环节发生

## API文档

启动后端服务后，访问 http://localhost:8000/docs 查看完整的API文档。

## 项目结构

```
easy-book/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API路由模块
│   │   │   ├── students.py # 学员管理API
│   │   │   ├── appointments.py # 预约管理API
│   │   │   └── attendance.py # 签到管理API
│   │   ├── models.py       # 数据模型定义
│   │   ├── services.py     # 业务逻辑层
│   │   ├── database.py     # 数据库连接配置
│   │   ├── mongo_database.py # MongoDB数据库操作
│   │   └── main.py         # FastAPI应用入口
│   ├── requirements.txt    # Python依赖包
│   └── .env               # 环境变量配置
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── api/            # API调用封装
│   │   │   ├── student.js  # 学员相关API
│   │   │   ├── appointment.js # 预约相关API
│   │   │   ├── attendance.js # 签到相关API
│   │   │   └── index.js    # Axios配置
│   │   ├── stores/         # Pinia状态管理
│   │   │   ├── student.js  # 学员状态
│   │   │   └── appointment.js # 预约状态
│   │   ├── views/          # 页面组件
│   │   │   ├── Home.vue    # 首页（预约管理）
│   │   │   ├── Students.vue # 学员列表页
│   │   │   ├── StudentDetail.vue # 学员详情页
│   │   │   └── AddStudent.vue # 添加学员页
│   │   ├── components/     # 公共组件
│   │   │   └── Toast.vue   # 消息提示组件
│   │   ├── utils/          # 工具函数
│   │   │   ├── date.js     # 日期处理
│   │   │   └── toast.js    # 消息提示
│   │   ├── router/         # 路由配置
│   │   │   └── index.js    # Vue Router配置
│   │   ├── App.vue         # 根组件
│   │   └── main.js         # 应用入口
│   ├── package.json        # Node.js依赖配置
│   ├── vite.config.js      # Vite构建配置
│   └── index.html          # HTML模板
├── doc/                    # 项目文档
│   ├── 01-需求分析/        # 需求分析文档
│   ├── 02-设计文档/        # 设计文档
│   │   ├── 后端设计.md     # 后端架构设计
│   │   ├── 前端设计.md     # 前端架构设计
│   │   ├── 数据库设计.md   # 数据库设计
│   │   └── UI设计.md       # 界面设计
│   ├── 03-技术文档/        # 技术文档
│   │   ├── 技术选型文档.md # 技术栈说明
│   │   ├── API接口文档.md   # API文档
│   │   └── MongoDB数据库迁移指南.md # 数据库迁移指南
│   ├── 04-测试文档/        # 测试文档
│   │   ├── 测试方案.md     # 测试计划
│   │   └── 功能测试报告.md # 测试报告
│   ├── 05-原型设计/        # 原型设计
│   │   └── 原型图.html     # 原型展示
│   └── 测试报告/           # 测试报告（按序号排序）
│       ├── 01-首页undefined问题测试报告.md
│       ├── 02-签到功能修复测试报告.md
│       └── ...             # 后续测试报告
├── README.md               # 项目说明文档
├── 安装指南.md             # 详细安装指南
├── start.bat              # Windows启动脚本
├── start.sh               # Linux/Mac启动脚本
└── .gitignore             # Git忽略文件配置
```

## 注意事项

1. 确保MongoDB服务正常运行
2. 首次使用需要先添加学员
3. 1v1课程在同一时间段不允许冲突
4. 系统设计为个人使用，不支持多用户

## 测试

### 自动化测试
项目包含完整的自动化测试套件，用于验证系统功能：

```bash
# 运行自动化测试
cd tests
python test_automation.py
```

**测试内容**：
- ✅ API健康检查
- ✅ 页面加载测试
- ✅ UI创建学生
- ✅ 创建预约
- ✅ 签到功能
- ✅ 页面UI更新
- ✅ 重复操作保护
- ✅ 预约冲突检查

**测试要求**：
- 确保后端服务运行在 http://localhost:8002
- 确保前端服务运行在 http://localhost:5173
- 确保MongoDB服务正常运行
- 安装必要的测试依赖：`pip install selenium pymongo requests`

**测试结果**：
- 成功率：75% (6/8 测试通过)
- 包含UI测试和API测试
- 自动生成测试报告

### 测试文件位置
- **自动化测试脚本**: `tests/test_automation.py`
- **测试报告**: `tests/test_reports/`
- **测试文档**: `doc/04-测试文档/`

## 开发说明

这是一个简化的demo版本，专注于核心功能实现。如需扩展功能，可以参考 `doc/` 目录下的设计文档。

## 许可证

MIT License