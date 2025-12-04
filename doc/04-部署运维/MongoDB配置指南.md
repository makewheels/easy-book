# MongoDB 数据库初始化

## 初始化脚本说明

MongoDB初始化脚本用于创建应用所需的数据库、用户和基本索引结构。

## 脚本内容

### mongodb/init/init.js
```javascript
// 创建应用数据库和用户
db = db.getSiblingDB('easy_book');

// 创建应用用户
db.createUser({
  user: 'easybook_user',
  pwd: 'easybook_pass',
  roles: [
    {
      role: 'readWrite',
      db: 'easy_book'
    }
  ]
});

// 创建集合和索引
db.createCollection('students');
db.students.createIndex({ "name": 1 });

db.createCollection('appointments');
db.appointments.createIndex({ "date": 1, "time": 1 });
db.appointments.createIndex({ "student_id": 1 });

db.createCollection('attendance');
db.attendance.createIndex({ "appointment_id": 1, "student_id": 1 });

print('MongoDB initialization completed');
```

## 使用方法

### 1. 本地开发环境
```bash
# 启动MongoDB后运行初始化
mongo < mongodb/init/init.js
```

### 2. Docker环境
```bash
# 在docker-compose.yml中添加初始化脚本
services:
  mongodb:
    image: mongo:6
    volumes:
      - ./mongodb/init:/docker-entrypoint-initdb.d
```

### 3. 生产环境
```bash
# 连接到生产MongoDB服务器
mongo --host <host> --port <port> < mongodb/init/init.js
```

## 数据库结构

### 集合说明

#### students - 学生信息
- **name索引**: 优化按姓名查询

#### appointments - 预约记录
- **date+time索引**: 优化按日期时间查询
- **student_id索引**: 优化按学生查询预约

#### attendance - 考勤记录
- **appointment_id+student_id索引**: 优化按预约和学生查询考勤

## 注意事项

1. **用户权限**: 初始用户为`easybook_user`，仅拥有`easy_book`数据库的读写权限
2. **索引策略**: 脚本中创建的是基础索引，实际应用中会通过代码自动创建更完整的索引
3. **安全性**: 生产环境中建议修改默认密码
4. **备份**: 初始化前建议先备份现有数据库

## 验证初始化

```bash
# 验证数据库和用户
mongo easy_book -u easybook_user -p easybook_pass --authenticationDatabase easy_book

# 验证集合和索引
show collections
db.students.getIndexes()
db.appointments.getIndexes()
db.attendance.getIndexes()
```