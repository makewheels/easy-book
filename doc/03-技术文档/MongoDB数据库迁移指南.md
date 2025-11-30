# MongoDB数据库迁移指南

## 概述
项目已从文件存储（JSON文件）迁移到真正的MongoDB数据库。

## 修改内容

### 1. 新增文件
- `backend/app/mongo_database.py` - MongoDB数据库操作类
- `backend/.env` - 数据库连接配置文件

### 2. 修改文件
- `backend/app/database.py` - 改为导入MongoDB数据库实现
- `backend/app/main.py` - 添加环境变量加载

## 数据库要求

### MongoDB安装
1. **Windows**: 下载并安装MongoDB Community Server
2. **Mac**: `brew install mongodb-community`
3. **Linux**: `sudo apt-get install mongodb`

### 启动MongoDB服务
1. **Windows**: 在服务中启动MongoDB
2. **Mac/Linux**: `brew services start mongodb-community` 或 `sudo systemctl start mongod`

### Docker方式（推荐）
```bash
docker run -d --name mongodb -p 27017:27017 mongo:6
```

## 配置说明

### 环境变量配置 (.env文件)
```
MONGODB_URL=mongodb://localhost:27017
DB_NAME=easy_book
```

### 认证配置（可选）
如果MongoDB启用了认证：
```
MONGODB_URL=mongodb://username:password@localhost:27017
DB_NAME=easy_book
```

## 数据库结构

### 集合（Collections）
1. **students** - 学生信息
   - `_id`: 学生ID
   - `name`: 姓名
   - `phone`: 电话
   - `total_lessons`: 总课程数
   - `remaining_lessons`: 剩余课程数
   - `package_type`: 套餐类型
   - `learning_item`: 学习项目
   - `price`: 价格
   - `venue_share`: 场地分成
   - `profit`: 利润
   - `create_time`: 创建时间
   - `update_time`: 更新时间

2. **appointments** - 预约记录
   - `_id`: 预约ID
   - `student_id`: 学生ID
   - `appointment_date`: 预约日期
   - `time_slot`: 时间段
   - `status`: 状态 (scheduled/checked/absent/cancelled)
   - `create_time`: 创建时间
   - `update_time`: 更新时间

3. **attendances** - 考勤记录
   - `_id`: 考勤ID
   - `student_id`: 学生ID
   - `appointment_id`: 预约ID
   - `attendance_date`: 考勤日期
   - `time_slot`: 时间段
   - `status`: 状态 (checked/absent)
   - `lessons_before`: 课前剩余课程
   - `lessons_after`: 课后剩余课程
   - `create_time`: 创建时间

## 索引优化

系统会自动创建以下索引：
1. **students集合**:
   - `name` (唯一索引)
   - `phone` (唯一索引)

2. **appointments集合**:
   - `student_id + appointment_date + time_slot` (复合唯一索引)
   - `appointment_date` (单字段索引)

3. **attendances集合**:
   - `student_id + appointment_id` (复合唯一索引)
   - `attendance_date` (单字段索引)

## 数据迁移

### 从JSON文件迁移到MongoDB
如果需要从现有的JSON文件迁移数据：

1. 确保MongoDB服务正在运行
2. 启动应用程序（会自动创建数据库和索引）
3. 使用以下脚本迁移数据（可选）：

```python
import json
import asyncio
from app.mongo_database import connect_to_mongo, get_database

async def migrate_data():
    await connect_to_mongo()
    db = get_database()
    
    # 迁移学生数据
    if os.path.exists("data/students.json"):
        with open("data/students.json", 'r', encoding='utf-8') as f:
            students = json.load(f)
            for student_id, student_data in students.items():
                await db.create_student(student_data)
    
    # 迁移预约数据
    if os.path.exists("data/appointments.json"):
        with open("data/appointments.json", 'r', encoding='utf-8') as f:
            appointments = json.load(f)
            for apt_id, apt_data in appointments.items():
                await db.create_appointment(apt_data)
    
    # 迁移考勤数据
    if os.path.exists("data/attendances.json"):
        with open("data/attendances.json", 'r', encoding='utf-8') as f:
            attendances = json.load(f)
            for att_id, att_data in attendances.items():
                await db.create_attendance(att_data)

# 运行迁移
asyncio.run(migrate_data())
```

## 优势

### 相比文件存储的优势
1. **性能**: MongoDB查询性能远优于JSON文件读写
2. **并发**: 支持多用户并发访问
3. **扩展性**: 支持水平扩展和分片
4. **查询**: 支持复杂查询和聚合操作
5. **事务**: 支持ACID事务
6. **索引**: 自动索引优化查询性能
7. **备份**: 支持专业备份和恢复工具

## 故障排除

### 常见问题
1. **连接失败**: 检查MongoDB服务是否启动，端口是否正确
2. **权限错误**: 检查MongoDB认证配置
3. **索引创建失败**: 检查数据完整性，确保唯一字段无重复

### 调试方法
1. 检查应用日志中的数据库连接信息
2. 使用MongoDB Compass连接查看数据库
3. 检查`.env`文件配置是否正确

## 清理

### 删除data目录（可选）
迁移完成后，可以删除`backend/data`目录：
```bash
rm -rf backend/data
```

### 保留memory_database.py
建议保留`memory_database.py`文件作为备用方案。