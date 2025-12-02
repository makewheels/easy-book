# Easy Book 自动化测试

本目录包含 Easy Book 项目的专业自动化测试套件。

## 📁 文件结构

```
tests/
├── README.md                    # 自动化测试说明文档
├── test_requirements.txt       # Python依赖列表
├── automation.py               # 专业自动化测试套件
├── install_deps.bat             # Windows依赖安装脚本
└── run_test.bat                # Windows测试运行脚本
```

## 🧪 专业自动化测试 (`automation.py`)

这是一个完整的自动化测试套件，包含：

### ✅ 测试覆盖范围

1. **API健康检查** - 验证后端服务状态
2. **页面加载测试** - 验证前端页面正常加载
3. **UI创建学生** - 通过界面创建学生
4. **创建预约** - 通过API创建预约
5. **签到功能** - 测试签到逻辑和课程扣减
6. **页面UI更新** - 验证状态正确显示
7. **重复操作防护** - 验证重复签到/缺席的防护

### ✅ 测试技术栈

- **Selenium**: UI界面自动化测试
- **Requests**: HTTP API接口测试
- **PyMongo**: MongoDB数据库验证
- **ChromeDriver**: 浏览器自动化
- **专业断言**: 明确的成功/失败判断

### ✅ 测试特点

- **完整断言**: `assert_true`, `assert_equal`, `assert_contains`
- **自动清理**: 测试后自动删除测试数据
- **环境管理**: 自动初始化和清理
- **详细报告**: 测试通过/失败统计
- **错误信息**: 具体的失败原因

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