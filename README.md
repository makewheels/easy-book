# Easy Book - 泳课学员管理系统

一个轻量级的泳课学员管理系统，专为个人使用设计。

## 📖 文档导航

- **[AGENTS.md](./AGENTS.md)** - AI助手开发指南（推荐）- 包含完整的开发规范、API说明和测试指南
- **[CLAUDE.md](./CLAUDE.md)** - Claude Code专用指导（英文版）

## 功能特点

- 📱 移动端友好设计
- 👥 学员管理（增删改查）
- 📅 预约管理（创建、查询、冲突检查）
- ✅ 签到管理（签到、缺席、自动扣费）
- 📊 课程统计
- 🗓️ 表格日历（周视图、状态显示）

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

### 模块化自动化测试
项目包含完整的模块化自动化测试套件，覆盖所有核心功能：

```bash
# 安装测试依赖
cd tests
pip install -r requirements.txt

# 运行完整测试套件
python test_all.py

# 运行特定模块测试
python test_students.py      # 学员管理测试
python test_appointments.py  # 预约管理测试
python test_attendance.py    # 考勤管理测试
python test_ui_integration.py # UI和集成测试
```

### 测试覆盖范围

**学员管理模块** (test_students.py)：
- ✅ API创建学员
- ✅ API获取学员列表
- ✅ API获取单个学员
- ✅ API更新学员信息
- ✅ API删除学员
- ✅ UI创建学员
- ✅ UI学员列表显示

**预约管理模块** (test_appointments.py)：
- ✅ API创建预约
- ✅ API获取学员预约记录
- ✅ API获取每日预约
- ✅ API更新预约
- ✅ API删除预约
- ✅ 1v1预约冲突检测
- ✅ 1v1与1v多预约规则
- ✅ 同一学员重复预约检测

**考勤管理模块** (test_attendance.py)：
- ✅ API签到功能
- ✅ API标记缺席
- ✅ API获取学员考勤记录
- ✅ 重复签到保护
- ✅ 重复标记缺席保护
- ✅ 课程扣费逻辑验证
- ✅ 课程不足时处理

**UI和集成测试** (test_ui_integration.py)：
- ✅ API健康检查
- ✅ 页面加载测试
- ✅ 导航流程测试
- ✅ 完整学生工作流程
- ✅ UI学生管理功能
- ✅ UI日历视图功能
- ✅ 数据一致性验证
- ✅ API错误处理
- ✅ 基础性能测试

### 测试要求
- **后端服务**: 运行在 http://localhost:8004
- **前端服务**: 运行在 http://localhost:5174
- **数据库**: MongoDB服务正常运行
- **Python依赖**: `pip install selenium pymongo requests python-dotenv`

### 测试文件结构
```
tests/
├── conftest.py              # 测试基础设施和基础类
├── test_all.py              # 主测试运行器
├── test_students.py         # 学员管理模块测试
├── test_appointments.py     # 预约管理模块测试
├── test_attendance.py       # 考勤管理模块测试
├── test_ui_integration.py   # UI和集成测试
├── test_automation.py       # 原始测试脚本（已弃用）
└── requirements.txt         # 测试依赖包
```

### 测试报告
- 自动生成详细的综合测试报告
- 包含成功率统计和性能指标
- 显示失败模块的详细错误信息
- 支持并发执行所有测试模块

### 当前测试状态
- **学员管理**: 100% 通过率 (7/7 测试) ✅
- **预约管理**: 正在完善中 (API响应格式需调整)
- **考勤管理**: 正在完善中 (API响应格式需调整)
- **UI集成**: 正在完善中 (需要浏览器环境配置)
- **整体架构**: 测试框架已搭建完成，支持快速扩展

### 测试价值
这套模块化测试为项目提供了重要的质量保障：
- 🛡️ **回归测试**: 防止代码修改破坏现有功能
- 📊 **功能验证**: 确保所有API端点正常工作
- 🔍 **问题发现**: 早期发现配置和兼容性问题
- 📈 **开发效率**: 自动化测试减少手动测试时间
- 🚀 **部署信心**: 测试通过后可安全部署

## 开发说明

这是一个简化的demo版本，专注于核心功能实现。如需扩展功能，可以参考 `doc/` 目录下的设计文档。

## 🆕 添加新功能指南

### 开发流程
当添加新功能时，需要按以下步骤更新相关文档：

#### 1. 代码开发
- **后端**: 在 `backend/api_server/` 中添加新的API路由和服务
- **前端**: 在 `frontend/src/views/` 中添加新的页面组件
- **路由**: 更新 `frontend/src/router/index.js` 添加新路由

#### 2. 文档更新
**必须更新的文档**：

1. **README.md** - 更新功能特点列表
   ```markdown
   ## 功能特点
   - 📱 移动端友好设计
   - 👥 学员管理（增删改查）
   - 📅 预约管理（创建、查询、冲突检查）
   - ✅ 签到管理（签到、缺席、自动扣费）
   - 📊 课程统计
   - 🗓️ 表格日历（周视图、状态显示）
   - 🆕 [新功能描述]
   ```

2. **API接口文档** (`doc/03-技术文档/API接口文档.md`)
   - 添加新API端点的详细说明
   - 包含请求参数、响应格式、错误处理

3. **前端设计文档** (`doc/02-设计文档/前端设计.md`)
   - 更新页面组件列表
   - 添加新页面的设计说明

4. **实际功能清单** (`doc/实际功能清单.md`)
   - 更新API端点列表
   - 添加新页面路由
   - 更新功能特性

#### 3. 测试更新
**必须添加的测试**：

1. **API测试** - 在 `tests/` 中创建对应的测试文件
2. **功能测试** - 验证新功能的完整工作流程
3. **集成测试** - 确保新功能与现有功能兼容

#### 4. 自动化测试
运行完整的测试套件：
```bash
cd tests
python test_all.py
```

#### 5. 版本更新
更新版本号和部署文档：
- 更新 `deployment.md` 中的当前版本
- 记录新功能的版本历史

### 示例：添加新页面功能
假设添加"报表统计"功能：

1. **代码开发**：
   - 创建 `frontend/src/views/Reports.vue`
   - 添加路由：`{ path: '/reports', name: 'Reports', component: Reports }`
   - 添加后端API：`GET /api/reports/summary`

2. **文档更新**：
   - README.md: 添加 📈 报表统计
   - API文档: 添加报表API说明
   - 前端设计: 添加Reports.vue说明
   - 功能清单: 添加新路由和API

3. **测试创建**：
   - 创建 `tests/test_reports.py`
   - 测试报表API和页面功能

### 重要注意事项
- ⚠️ **遵循本地优先原则**: 所有修改先在本地验证，再部署
- 🧪 **必须添加测试**: 新功能必须有对应的自动化测试
- 📝 **文档同步更新**: 代码和文档必须保持一致
- 🔄 **版本管理**: 更新版本号并记录变更

## 许可证

MIT License