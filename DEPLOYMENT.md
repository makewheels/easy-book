# Easy Book 部署文档

## 服务器信息
- **服务器IP**: 49.233.60.29
- **用户**: ubuntu
- **项目路径**: /home/admin/easy-book

## 服务架构
- **前端**: Vue 3 + Vite (通过 nginx 80端口服务)
- **后端**: FastAPI + MongoDB (运行在 8002端口)
- **数据库**: MongoDB (10.0.20.14:27017)

## 部署步骤

### 1. 后端部署
```bash
# 1. 进入后端目录
cd /home/admin/easy-book/backend/backend

# 2. 启动后端服务
nohup python3 run.py 8002 > /tmp/backend.log 2>&1 &

# 3. 检查服务状态
ps aux | grep "python3 run.py"
curl -s http://localhost:8002/health
```

### 2. 前端部署
```bash
# 1. 本地构建
cd frontend
npm run build

# 2. 打包上传
tar -czf frontend-dist.tar.gz -C dist .

# 3. 服务器部署
# 上传文件到服务器
# 解压到 /home/admin/easy-book/backend/frontend/dist/
```

### 3. Nginx配置
```bash
# 配置文件位置: /etc/nginx/sites-enabled/easy-book.conf

# 检查配置
sudo nginx -t

# 重新加载配置
sudo systemctl reload nginx
```

## 更新部署流程

### 后端更新
```bash
# 1. 本地打包后端代码
tar -czf backend-fix.tar.gz -C backend api_server

# 2. 上传到服务器
scp backend-fix.tar.gz ubuntu@49.233.60.29:/home/admin/easy-book/

# 3. 服务器部署
cd /home/admin/easy-book
tar -xzf backend-fix.tar.gz
cp -r api_server /home/admin/easy-book/backend/backend/

# 4. 重启后端服务
pkill -f "python3 run.py"
cd /home/admin/easy-book/backend/backend
nohup python3 run.py 8002 > /tmp/backend.log 2>&1 &

# 5. 验证部署
curl -s http://49.233.60.29/health
```

### 前端更新
```bash
# 1. 本地修改代码
# 2. 构建
cd frontend && npm run build

# 3. 部署
tar -czf frontend-dist.tar.gz -C dist .
scp frontend-dist.tar.gz ubuntu@49.233.60.29:/home/admin/easy-book/

# 4. 服务器更新
cd /home/admin/easy-book/backend/frontend
rm -rf dist/*
tar -xzf /home/admin/easy-book/frontend-dist.tar.gz -C dist
```

## 服务管理

### 查看服务状态
```bash
# 后端服务
ps aux | grep "python3 run.py"
curl -s http://localhost:8002/health

# Nginx服务
sudo systemctl status nginx

# 数据库连接
curl -s http://localhost:8002/api/health
```

### 日志查看
```bash
# 后端日志
tail -f /tmp/backend.log

# Nginx访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx错误日志
sudo tail -f /var/log/nginx/error.log
```

### 重启服务
```bash
# 重启后端
pkill -f "python3 run.py"
cd /home/admin/easy-book/backend/backend
nohup python3 run.py 8002 > /tmp/backend.log 2>&1 &

# 重启Nginx
sudo systemctl reload nginx
```

## 常见问题解决

### 1. 后端无法启动
- 检查端口是否被占用: `netstat -tlnp | grep 8002`
- 查看错误日志: `tail /tmp/backend.log`
- 检查环境变量和配置文件

### 2. API 404错误
- 检查nginx配置是否正确加载
- 验证nginx主配置是否包含 `include /etc/nginx/sites-enabled/*;`
- 测试后端直接访问: `curl http://localhost:8002/api/students/`

### 3. 数据库连接问题
- 检查MongoDB服务状态
- 验证连接字符串
- 检查数据库索引和权限

### 4. 前端页面无法访问
- 检查nginx配置中的静态文件路径
- 验证前端构建文件是否正确部署
- 查看nginx错误日志

## 数据库操作
```bash
# 连接数据库
python3 -c "
from pymongo import MongoClient
client = MongoClient('mongodb://easy-book:JYWSRNKNJ0JFlQGn6H1@10.0.20.14:27017/easy_book?authSource=admin')
db = client.easy_book
print('Database connected successfully')
"

# 备份数据库
mongodump --host 10.0.20.14:27017 --username easy-book --password JYWSRNKNJ0JFlQGn6H1 --authenticationDatabase admin --db easy_book --out /backup/$(date +%Y%m%d)

# 查看集合索引
python3 -c "
from pymongo import MongoClient
client = MongoClient('mongodb://easy-book:JYWSRNKNJ0JFlQGn6H1@10.0.20.14:27017/easy_book?authSource=admin')
db = client.easy_book
print('Students indexes:', list(db.students.list_indexes()))
print('Appointments indexes:', list(db.appointments.list_indexes()))
print('Attendances indexes:', list(db.attendances.list_indexes()))
"
```

## 测试验证
```bash
# 测试API
curl -s http://49.233.60.29/api/students/ | python -m json.tool
curl -s http://49.233.60.29/api/appointments/daily/$(date +%Y-%m-%d) | python -m json.tool
curl -s http://49.233.60.29/health

# 测试前端
curl -s http://49.233.60.29/ | head -10
```