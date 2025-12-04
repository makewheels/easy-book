# Easy Book 测试项目

> 🧪 **独立的测试项目，可脱离前后端单独运行**

## 🎯 项目特点

这是一个**独立的测试项目**，具备以下特点：

- ✅ **完全独立**：可以脱离前后端项目单独运行
- ✅ **环境自包含**：包含独立的依赖管理和配置
- ✅ **分层测试**：单元测试、集成测试、功能特性测试
- ✅ **自动报告**：生成详细的测试报告
- ✅ **跨平台**：支持 Windows、Linux、Mac

## 📁 测试结构

### 📂 核心文件
- **[conftest.py](./conftest.py)** - 测试基础设施和配置
- **[requirements.txt](./requirements.txt)** - 测试依赖包
- **[test_all.py](./test_all.py)** - 主测试运行器

### 📂 测试分层

#### 🔧 utils/ - 测试工具包
- **[__init__.py](./utils/__init__.py)** - 工具包初始化
- **[test_base.py](./utils/test_base.py)** - 基础测试类，提供通用功能

#### 🧪 unit/ - 单元测试
测试单个功能模块的基本功能
- **[test_students.py](./unit/test_students.py)** - 学员管理模块测试 (7个测试)
- **[test_appointments.py](./unit/test_appointments.py)** - 预约管理模块测试 (14个测试)
- **[test_attendance.py](./unit/test_attendance.py)** - 考勤管理模块测试
- **[test_health.py](./unit/test_health.py)** - 健康检查和系统状态测试

#### 🔗 integration/ - 集成测试
测试模块间的集成和UI交互
- **[test_ui_integration.py](./integration/test_ui_integration.py)** - UI和集成测试
- **[test_api_integration.py](./integration/test_api_integration.py)** - API集成测试 (待添加)

#### ⭐ features/ - 功能特性测试
测试特定功能特性
- **[test_monday_restriction.py](./features/test_monday_restriction.py)** - 周一预约限制功能测试

#### 📊 reports/ - 测试报告
- **功能测试报告/** - 各模块功能测试报告
- **专项测试报告/** - 特定功能的专项测试报告
- **历史报告/** - 存档的历史测试报告

#### 📜 scripts/ - 测试脚本
- **[install_deps.bat](./scripts/install_deps.bat)** - 安装测试依赖脚本
- **[run_test.bat](./scripts/run_test.bat)** - 运行测试脚本

## 🚀 快速开始

### 运行所有测试
```bash
cd tests
python test_all.py
```

### 运行单个模块测试
```bash
cd tests
python unit/test_students.py      # 学员管理测试
python unit/test_appointments.py  # 预约管理测试
python integration/test_ui_integration.py  # UI集成测试
python features/test_monday_restriction.py  # 周一限制测试
```

### 安装测试依赖
```bash
cd tests
pip install -r requirements.txt
# 或使用脚本
scripts/install_deps.bat
```

## 📈 测试覆盖范围

### ✅ 学员管理模块 (unit/test_students.py)
- API创建学员
- API获取学员列表
- API获取单个学员
- API更新学员信息
- API删除学员
- UI创建学员
- UI学员列表显示

### ✅ 预约管理模块 (unit/test_appointments.py)
- API创建预约
- API获取学员预约记录
- API获取每日预约
- API更新预约
- API删除预约
- 1v1预约冲突检测
- 1v1与1v多预约规则
- 同一学员重复预约检测
- API获取即将到来的预约
- 前端统计准确性验证
- **🆕 预约时自动扣减课程**
- **🆕 取消预约时恢复课程**
- **🆕 课程不足时阻止预约**
- **🆕 多个预约扣减多个课程**

### ✅ 功能特性测试 (features/test_monday_restriction.py)
- 周一预约限制功能
- 前端验证逻辑
- 日历显示优化

## 🎯 测试策略

### 测试分层原则
1. **单元测试** - 测试单个API和业务逻辑
2. **集成测试** - 测试模块间交互和UI流程
3. **功能测试** - 测试完整的业务功能特性

### 测试覆盖目标
- **功能覆盖**: 所有业务功能都有对应测试
- **场景覆盖**: 正常流程和边界条件
- **接口覆盖**: 所有API端点都有测试验证
- **UI覆盖**: 关键用户界面操作有测试验证

## 🚀 快速开始

### 1. 安装依赖

**Windows 用户（推荐）:**

```bash
# 双击运行安装脚本
tests\install_deps.bat

# 或手动执行：
cd D:\workspace\python\easy-book
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r tests\test_requirements.txt
```

**Linux/Mac 用户:**

```bash
cd D:\workspace\python\easy-book
python -m venv .venv
source .venv/bin/activate
pip install -r tests/test_requirements.txt
```

### 2. 确保服务运行

```bash
# 启动后端服务（端口8002）
cd backend
python -m api_server.main 8002

# 启动前端服务（端口5173）
cd frontend
npm run dev

# 确保MongoDB运行
mongod
```

### 3. 运行自动化测试

**Windows 用户:**

```bash
# 双击运行测试脚本
tests\run_test.bat

# 或手动执行：
cd tests
..\.venv\Scripts\python.exe automation.py
```

**Linux/Mac 用户:**

```bash
cd tests
python automation.py
```

## 📊 测试报告示例

```
============================================================
AUTO: Easy Book Professional Automation Test
============================================================
INIT: Initializing automation test environment...
PASS: Chrome browser initialized successfully
PASS: MongoDB connection successful
PASS: Test environment initialization complete

==================== API Health Check ====================
TEST: Test 1: API health check
PASS: API health check status code: 200
PASS: API health status: healthy
PASS: Test 1 passed: API health check normal
SUCCESS: API Health Check - PASSED

==================== Page Loading Test ====================
TEST: Test 2: Page loading test
PASS: Test 2 passed: Page loading normal
SUCCESS: Page Loading Test - PASSED

...

============================================================
REPORT: Test Report
============================================================
STAT: Total: 7 tests
PASS: 7 tests passed
FAIL: 0 tests failed
REPORT: Success rate: 100.0%

SUCCESS: All tests passed! System functionality normal!
```

## 🔧 测试环境要求

- **Python 3.8+**
- **Chrome浏览器**
- **MongoDB数据库**
- **后端API服务** (http://localhost:8002)
- **前端开发服务** (http://localhost:5173)

## 📋 依赖安装指南

### 方法1: 直接安装
```bash
pip install selenium pymongo requests webdriver-manager
```

### 方法2: 使用requirements.txt
```bash
pip install -r tests/test_requirements.txt
```

### 方法3: 如果遇到网络问题
```bash
pip install -r tests/test_requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

## 🐛 常见问题解决

### 1. Chrome浏览器问题
```bash
# 下载并安装Chrome浏览器
# Windows: https://www.google.com/chrome/
# Mac: brew install --cask google-chrome
# Linux: sudo apt-get install google-chrome-stable
```

### 2. 端口冲突
```bash
# Windows
netstat -ano | findstr :8002
taskkill /F /PID <进程ID>

# Linux/Mac
lsof -i :8002
kill -9 <进程ID>
```

### 3. MongoDB连接问题
```bash
# 检查MongoDB状态
mongo --eval "db.adminCommand('ismaster')"

# 启动MongoDB
mongod
```

### 4. 虚拟环境问题
```bash
# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 查看Python路径
which python
python --version
```

## 🎯 测试验证内容

### API功能测试
- ✅ 健康检查接口
- ✅ 学生创建接口
- ✅ 预约创建接口
- ✅ 签到接口
- ✅ 缺席接口

### UI功能测试
- ✅ 页面加载
- ✅ 表单填写
- ✅ 按钮点击
- ✅ 状态显示

### 数据库验证
- ✅ 学生数据存储
- ✅ 预约数据存储
- ✅ 考勤记录存储
- ✅ 课程扣减逻辑

### 业务逻辑测试
- ✅ 签到扣课
- ✅ 缺席不扣课
- ✅ 重复操作防护
- ✅ 状态同步

## 🔄 持续集成

### GitHub Actions示例
```yaml
name: Automation Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r tests/test_requirements.txt

    - name: Start services
      run: |
        # 启动MongoDB
        sudo systemctl start mongod

        # 启动后端
        cd backend && python -m api_server.main 8002 &

        # 启动前端
        cd frontend && npm run dev &
        sleep 10

    - name: Run automation tests
      run: |
        cd tests
        python automation.py
```

## 📞 支持和帮助

如需帮助或报告问题，请：

1. 查看详细的错误日志
2. 检查服务是否正常启动
3. 确认依赖已正确安装
4. 参考项目的部署文档

---

**注意**: 这个自动化测试是专业的端到端测试，会实际操作浏览器界面和数据库，请确保测试环境干净。