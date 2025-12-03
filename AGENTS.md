# AGENTS.md

本文件为AI助手（如Claude Code、GitHub Copilot等）在此代码仓库中工作时提供指导。

## 项目概述

Easy Book是一个轻量级的泳课学员管理系统，专为个人使用设计。系统由FastAPI后端、MongoDB数据库和Vue 3前端组成，针对移动设备进行了优化。

## 架构设计

### 后端 (Python + FastAPI)
- **框架**: FastAPI，采用async/await异步模式
- **数据库**: MongoDB，使用PyMongo驱动
- **结构**: 模块化设计，代码位于`backend/api_server/`目录
  - `main.py`: FastAPI应用入口点
  - `models.py`: 学生、预约和考勤的Pydantic数据模型
  - `services.py`: 业务逻辑层（StudentService、AppointmentService、AttendanceService）
  - `database.py` & `mongo_database.py`: MongoDB连接和操作
  - `api/`: 路由模块（students.py、appointments.py、attendance.py）

### 前端 (Vue 3)
- **框架**: Vue 3 + Composition API
- **构建工具**: Vite
- **状态管理**: Pinia状态管理
- **移动优先**: 针对移动设备设计的响应式布局
- **结构**:
  - `src/views/`: 主要页面（Home.vue、Students.vue、StudentDetail.vue、AddStudent.vue）
  - `src/api/`: 基于Axios的API客户端模块
  - `src/stores/`: Pinia状态管理
  - `src/utils/`: 工具函数（date.js、toast.js）

## 开发环境配置

### 后端开发
```bash
# 进入后端目录
cd backend

# 安装Python依赖
pip install -r requirements.txt

# 运行开发服务器（默认端口8002）
python -m api_server.main

# 使用自定义端口运行
python -m api_server.main 8003
```

### 前端开发
```bash
# 进入前端目录
cd frontend

# 安装Node.js依赖
npm install

# 运行开发服务器（端口5173）
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

### 数据库设置
```bash
# 使用Docker（推荐）
docker run -d --name mongodb -p 27017:27017 mongo:6

# 或在本地安装MongoDB
mongod
```

## 核心开发模式

### 后端模式
1. **服务层模式**: 所有业务逻辑封装在服务类中（StudentService、AppointmentService、AttendanceService）
2. **Pydantic模型**: 所有数据验证和序列化使用`models.py`中的Pydantic模型
3. **异步模式**: 所有数据库操作和API端点使用async/await模式
4. **MongoDB操作**: 通过`mongo_database.py`中的自定义数据库抽象进行直接MongoDB操作

### 前端模式
1. **Composition API**: 所有Vue组件使用`<script setup>`和Composition API
2. **Pinia状态管理**: 通过模块化Pinia stores进行状态管理
3. **API代理**: 前端使用Vite代理将`/api/*`请求转发到后端`localhost:8002`
4. **移动优化**: 触摸友好的界面，底部导航

### 数据流
1. **学员管理**: 学员的CRUD操作，包含课程跟踪
2. **预约系统**: 基于日期的调度，1v1课程冲突检测
3. **考勤跟踪**: 签到/签出系统，自动扣减课程
4. **冲突解决**: 1v1课程在同一时间段不能重叠

## API端点结构

- **学员管理**: `/api/students/` - 完整的CRUD操作
- **预约管理**: `/api/appointments/` - 创建、按学员查询、按日期查询
- **考勤管理**: `/api/attendance/` - 签到和标记缺席功能
- **健康检查**: `/health`和`/api/health/db`用于服务监控

## 配置文件

- **后端**: `backend/.env` - MongoDB连接设置
- **前端**: `frontend/vite.config.js` - 包含API代理的Vite配置
- **数据库**: 使用MongoDB连接字符串格式`mongodb://localhost:27017`

## 业务逻辑

### 预约冲突规则
- 1v1课程在同一时间段不能与其他1v1课程冲突
- 1v多课程可以共享时间段
- 学员在同一时间段不能有多个预约

### 课程扣费规则
- 只有签到（`checked`状态）会扣减课程
- 缺席（`absent`状态）不会扣减课程
- 课程在签到时立即扣减

### 学员状态
- `total_lessons`: 原始套餐大小
- `remaining_lessons`: 当前可用课程数
- `attended_lessons`: 计算方式为`total_lessons - remaining_lessons`

## 移动端UI注意事项

- 触摸目标最小44px，符合iOS规范
- 底部导航便于拇指操作
- 支持日期导航的滑动手势
- 响应式设计适配桌面屏幕（最大宽度430px）

## 测试和质量保证

- API文档可在`http://localhost:8002/docs`访问（后端运行时）
- FastAPI提供自动OpenAPI模式生成
- 前端通过Axios拦截器进行错误处理，提供用户友好的消息

## 添加新功能指南

### 开发流程
当添加新功能时，需要按以下步骤更新相关文档：

#### 1. 代码开发
- **后端**: 在`backend/api_server/`中添加新的API路由和服务
- **前端**: 在`frontend/src/views/`中添加新的页面组件
- **路由**: 更新`frontend/src/router/index.js`添加新路由

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

1. **API测试** - 在`tests/`中创建对应的测试文件
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
- 更新`deployment.md`中的当前版本
- 记录新功能的版本历史

### 示例：添加新页面功能
假设添加"报表统计"功能：

1. **代码开发**：
   - 创建`frontend/src/views/Reports.vue`
   - 添加路由：`{ path: '/reports', name: 'Reports', component: Reports }`
   - 添加后端API：`GET /api/reports/summary`

2. **文档更新**：
   - README.md: 添加📈 报表统计
   - API文档: 添加报表API说明
   - 前端设计: 添加Reports.vue说明
   - 功能清单: 添加新路由和API

3. **测试创建**：
   - 创建`tests/test_reports.py`
   - 测试报表API和页面功能

### 重要注意事项
- ⚠️ **遵循本地优先原则**: 所有修改先在本地验证，再部署
- 🧪 **必须添加测试**: 新功能必须有对应的自动化测试
- 📝 **文档同步更新**: 代码和文档必须保持一致
- 🔄 **版本管理**: 更新版本号并记录变更

## 项目约定

### 代码规范
- **注释语言**: 所有代码注释使用中文
- **界面语言**: 所有用户界面文本使用中文
- **文档语言**: 所有文档使用中文编写
- **国际化**: 项目不需要国际化支持

### 开发流程
- **本地开发**: 所有代码修改先在本地测试
- **测试验证**: 确保测试用例通过后再部署
- **文档同步**: 代码修改后同步更新相关文档
- **避免表情符号**: 不使用emoji，防止乱码问题

### 部署规范
- **测试环境**: 先在测试环境验证所有功能
- **生产部署**: 测试通过后部署到生产服务器
- **版本控制**: 记录每次部署的版本和变更内容

## 相关文档

- `CLAUDE.md` - Claude Code专用指导文件（本文件的英文版本）
- `README.md` - 项目主要说明文档
- `doc/`目录 - 详细的设计和技术文档