# Easy Book - 泳课学员管理系统 API接口文档

## 1. 接口概述

本文档描述了Easy Book泳课学员管理系统的RESTful API接口，包括学员管理、预约管理、签到管理等核心功能的接口规范。

### 1.1 基础信息

- **Base URL**: `http://localhost:8002/api`
- **API版本**: v1
- **数据格式**: JSON
- **字符编码**: UTF-8
- **实际运行端口**: 8002 (重要：不是8000)

### 1.2 通用响应格式

**成功响应**
```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    // 具体数据内容
  }
}
```

**错误响应**
```json
{
  "code": 400,
  "message": "错误描述",
  "details": "详细错误信息(可选)"
}
```

### 1.3 HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 500 | 服务器内部错误 |

## 2. 学员管理接口

### 2.1 获取学员列表

**接口地址**: `GET /api/students`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| size | int | 否 | 每页数量，默认20 |
| keyword | string | 否 | 搜索关键词(姓名/别称) |
| learning_item | string | 否 | 学习项目筛选 |
| package_type | string | 否 | 套餐类型筛选(1v1/1v多) |

**请求示例**:
```http
GET /api/students?page=1&size=20&learning_item=蛙泳
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "total": 15,
    "page": 1,
    "size": 20,
    "items": [
      {
        "id": "1",
        "name": "刘晓明",
        "nickname": "小明",
        "learning_item": "蛙泳",
        "package_type": "1v1",
        "total_lessons": 12,
        "remaining_lessons": 10,
        "price": 200,
        "venue_share": 120,
        "profit": 80,
        "note": "初学者，需要多练习",
        "create_time": "2024-01-15T10:00:00Z",
        "update_time": "2024-01-15T10:00:00Z",
        "next_appointment": "12-01 08:00",
        "attended_lessons": 2
      }
    ]
  }
}
```

### 2.2 创建学员

**接口地址**: `POST /api/students`

**请求参数**:
```json
{
  "name": "张三",
  "nickname": "小张",
  "learning_item": "蛙泳",
  "package_type": "1v1",
  "total_lessons": 10,
  "price": 200,
  "venue_share": 120,
  "note": "备注信息"
}
```

**参数说明**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| name | string | 是 | 姓名，1-50字符 |
| nickname | string | 否 | 别称，0-50字符 |
| learning_item | string | 是 | 学习项目 |
| package_type | string | 是 | 套餐类型(1v1/1v多) |
| total_lessons | int | 是 | 总课程数，大于0 |
| price | int | 是 | 售价(元)，大于0 |
| venue_share | int | 是 | 上交俱乐部(元)，大于等于0 |
| note | string | 否 | 备注，0-500字符 |

**响应示例**:
```json
{
  "code": 201,
  "message": "创建成功",
  "data": {
    "id": "2",
    "name": "张三",
    "nickname": "小张",
    "learning_item": "蛙泳",
    "package_type": "1v1",
    "total_lessons": 10,
    "remaining_lessons": 10,
    "price": 200,
    "venue_share": 120,
    "profit": 80,
    "note": "备注信息",
    "create_time": "2024-01-16T10:00:00Z",
    "update_time": "2024-01-16T10:00:00Z"
  }
}
```

### 2.3 获取学员详情

**接口地址**: `GET /api/students/{id}`

**路径参数**:
| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | string | 学员ID |

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": "1",
    "name": "刘晓明",
    "nickname": "小明",
    "learning_item": "蛙泳",
    "package_type": "1v1",
    "total_lessons": 12,
    "remaining_lessons": 10,
    "price": 200,
    "venue_share": 120,
    "profit": 80,
    "note": "初学者，需要多练习",
    "create_time": "2024-01-15T10:00:00Z",
    "update_time": "2024-01-15T10:00:00Z",
    "attended_lessons": 2
  }
}
```

### 2.4 更新学员信息

**接口地址**: `PUT /api/students/{id}`

**路径参数**:
| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | string | 学员ID |

**请求参数**:
```json
{
  "name": "刘晓明",
  "nickname": "明明",
  "learning_item": "自由泳",
  "note": "进步很快，已学会自由泳"
}
```

**参数说明**: 所有字段都是可选的，只更新传入的字段

**响应示例**:
```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": "1",
    "name": "刘晓明",
    "nickname": "明明",
    "learning_item": "自由泳",
    "package_type": "1v1",
    "total_lessons": 12,
    "remaining_lessons": 10,
    "price": 200,
    "venue_share": 120,
    "profit": 80,
    "note": "进步很快，已学会自由泳",
    "create_time": "2024-01-15T10:00:00Z",
    "update_time": "2024-01-20T10:00:00Z"
  }
}
```

### 2.5 删除学员

**接口地址**: `DELETE /api/students/{id}`

**路径参数**:
| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | string | 学员ID |

**响应示例**:
```json
{
  "code": 200,
  "message": "删除成功"
}
```

## 3. 预约管理接口

### 3.1 创建预约

**接口地址**: `POST /api/appointments`

**请求参数**:
```json
{
  "student_id": "1",
  "appointment_date": "2024-12-01",
  "time_slot": "08:00"
}
```

**参数说明**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| student_id | string | 是 | 学员ID |
| appointment_date | string | 是 | 预约日期(YYYY-MM-DD) |
| time_slot | string | 是 | 时间段(HH:MM) |

**响应示例**:
```json
{
  "code": 201,
  "message": "预约创建成功",
  "data": {
    "id": "1",
    "student_id": "1",
    "appointment_date": "2024-12-01",
    "time_slot": "08:00",
    "status": "scheduled",
    "create_time": "2024-01-15T10:00:00Z",
    "update_time": "2024-01-15T10:00:00Z"
  }
}
```

**错误响应(预约冲突)**:
```json
{
  "code": 409,
  "message": "时间段 08:00 已有1v1预约",
  "details": "该时间段已存在其他1v1学员预约，无法创建新的1v1预约"
}
```

### 3.2 获取学员预约记录

**接口地址**: `GET /api/appointments/student/{student_id}`

**路径参数**:
| 参数名 | 类型 | 说明 |
|--------|------|------|
| student_id | string | 学员ID |

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| future | bool | 否 | 是否只获取未来预约，默认false |
| page | int | 否 | 页码，默认1 |
| size | int | 否 | 每页数量，默认20 |

**请求示例**:
```http
GET /api/appointments/student/1?future=true&page=1&size=10
```

### 3.5 获取未来预约

**接口地址**: `GET /api/appointments/upcoming`

**查询参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| days | int | 否 | 获取未来天数，默认30天 |

**请求示例**:
```http
GET /api/appointments/upcoming?days=30
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取未来预约成功",
  "data": [
    {
      "date": "12-04",
      "weekday": "周四",
      "is_past": false,
      "slots": [
        {
          "time": "14:00",
          "students": [
            {
              "id": "693187485572014d9d226f6c",
              "name": "测试学员fwefww222",
              "package_type": "1v1",
              "learning_item": "自由泳",
              "attended_lessons": 7,
              "total_lessons": 10,
              "appointment_id": "693187485572014d9d226f6c",
              "student_id": "692bd03b58ba9900a7ac5b66",
              "status": "scheduled"
            }
          ]
        }
      ]
    }
  ]
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "total": 5,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": "1",
        "student_id": "1",
        "appointment_date": "2024-12-01",
        "time_slot": "08:00",
        "status": "scheduled",
        "create_time": "2024-01-15T10:00:00Z",
        "update_time": "2024-01-15T10:00:00Z",
        "student_info": {
          "name": "刘晓明",
          "learning_item": "蛙泳",
          "package_type": "1v1"
        }
      }
    ]
  }
}
```

### 3.3 获取某日所有预约

**接口地址**: `GET /api/appointments/daily/{date}`

**路径参数**:
| 参数名 | 类型 | 说明 |
|--------|------|------|
| date | string | 日期(YYYY-MM-DD) |

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "date": "2024-12-01",
    "weekday": "周日",
    "is_past": false,
    "slots": [
      {
        "time": "08:00",
        "students": [
          {
            "id": "1",
            "name": "刘晓明",
            "package_type": "1v1",
            "learning_item": "蛙泳",
            "attended_lessons": 2,
            "total_lessons": 12,
            "appointment_id": "1",
            "status": null
          }
        ]
      },
      {
        "time": "14:00",
        "students": [
          {
            "id": "3",
            "name": "陈思雨",
            "package_type": "1v多",
            "learning_item": "蛙泳",
            "attended_lessons": 3,
            "total_lessons": 8,
            "appointment_id": "3",
            "status": null
          },
          {
            "id": "4",
            "name": "张伟明",
            "package_type": "1v多",
            "learning_item": "自由泳",
            "attended_lessons": 7,
            "total_lessons": 15,
            "appointment_id": "4",
            "status": null
          }
        ]
      }
    ]
  }
}
```

### 3.4 修改预约

**接口地址**: `PUT /api/appointments/{id}`

**路径参数**:
| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | string | 预约ID |

**请求参数**:
```json
{
  "appointment_date": "2024-12-02",
  "time_slot": "09:00"
}
```

**参数说明**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| appointment_date | string | 否 | 新预约日期(YYYY-MM-DD) |
| time_slot | string | 否 | 新时间段(HH:MM) |

**响应示例**:
```json
{
  "code": 200,
  "message": "修改成功",
  "data": {
    "id": "1",
    "student_id": "1",
    "appointment_date": "2024-12-02",
    "time_slot": "09:00",
    "status": "scheduled",
    "create_time": "2024-01-15T10:00:00Z",
    "update_time": "2024-01-20T10:00:00Z"
  }
}
```

### 3.5 删除预约

**接口地址**: `DELETE /api/appointments/{id}`

**路径参数**:
| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | string | 预约ID |

**响应示例**:
```json
{
  "code": 200,
  "message": "删除成功"
}
```

## 4. 签到管理接口

### 4.1 学员签到

**接口地址**: `POST /api/attendance/checkin`

**请求参数**:
```json
{
  "appointment_id": "1",
  "student_id": "1"
}
```

**参数说明**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| appointment_id | string | 是 | 预约ID |
| student_id | string | 是 | 学员ID |

**响应示例**:
```json
{
  "code": 200,
  "message": "签到成功",
  "data": {
    "attendance_id": "1",
    "student_id": "1",
    "appointment_id": "1",
    "lessons_before": 10,
    "lessons_after": 9,
    "message": "签到成功，剩余课程：9"
  }
}
```

**错误响应(课程不足)**:
```json
{
  "code": 400,
  "message": "剩余课程不足",
  "details": "学员剩余课程为0，无法签到"
}
```

### 4.2 标记缺席

**接口地址**: `POST /api/attendance/absent`

**请求参数**:
```json
{
  "appointment_id": "1",
  "student_id": "1"
}
```

**参数说明**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| appointment_id | string | 是 | 预约ID |
| student_id | string | 是 | 学员ID |

**响应示例**:
```json
{
  "code": 200,
  "message": "标记缺席成功",
  "data": {
    "attendance_id": "1",
    "student_id": "1",
    "appointment_id": "1",
    "lessons_before": 10,
    "lessons_after": 10,
    "message": "已标记为缺席"
  }
}
```

### 4.3 获取学员上课记录

**接口地址**: `GET /api/attendance/student/{student_id}`

**路径参数**:
| 参数名 | 类型 | 说明 |
|--------|------|------|
| student_id | string | 学员ID |

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| size | int | 否 | 每页数量，默认20 |
| start_date | string | 否 | 开始日期(YYYY-MM-DD) |
| end_date | string | 否 | 结束日期(YYYY-MM-DD) |
| status | string | 否 | 出勤状态(checked/absent) |

**请求示例**:
```http
GET /api/attendance/student/1?page=1&size=10&start_date=2024-11-01&end_date=2024-11-30
```

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "total": 8,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": "1",
        "student_id": "1",
        "appointment_id": "1",
        "attendance_date": "2024-11-30",
        "time_slot": "08:00",
        "status": "checked",
        "lessons_before": 3,
        "lessons_after": 2,
        "create_time": "2024-11-30T08:30:00Z"
      },
      {
        "id": "2",
        "student_id": "1",
        "appointment_id": "2",
        "attendance_date": "2024-11-28",
        "time_slot": "08:00",
        "status": "absent",
        "lessons_before": 3,
        "lessons_after": 3,
        "create_time": "2024-11-28T08:30:00Z"
      }
    ]
  }
}
```

## 5. 统计分析接口

### 5.1 获取学员统计信息

**接口地址**: `GET /api/statistics/student/{student_id}`

**路径参数**:
| 参数名 | 类型 | 说明 |
|--------|------|------|
| student_id | string | 学员ID |

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "student_info": {
      "id": "1",
      "name": "刘晓明",
      "learning_item": "蛙泳",
      "package_type": "1v1",
      "total_lessons": 12,
      "remaining_lessons": 9
    },
    "attendance_stats": {
      "total_attended": 3,
      "total_absent": 1,
      "attendance_rate": 0.75,
      "next_appointment": {
        "date": "2024-12-01",
        "time": "08:00"
      }
    },
    "financial_stats": {
      "total_paid": 2400,
      "total_venue_share": 1440,
      "total_profit": 960,
      "per_lesson_cost": 200
    }
  }
}
```

### 5.2 获取整体统计信息

**接口地址**: `GET /api/statistics/overview`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| start_date | string | 否 | 开始日期(YYYY-MM-DD) |
| end_date | string | 否 | 结束日期(YYYY-MM-DD) |

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "student_stats": {
      "total_students": 15,
      "active_students": 12,
      "new_students_this_month": 3
    },
    "attendance_stats": {
      "total_attendances": 45,
      "total_attended": 38,
      "total_absent": 7,
      "attendance_rate": 0.84
    },
    "financial_stats": {
      "total_revenue": 9000,
      "total_venue_share": 5400,
      "total_profit": 3600
    },
    "learning_item_distribution": [
      {
        "item": "蛙泳",
        "count": 8,
        "percentage": 53.3
      },
      {
        "item": "自由泳",
        "count": 4,
        "percentage": 26.7
      },
      {
        "item": "踩水",
        "count": 3,
        "percentage": 20.0
      }
    ]
  }
}
```

## 6. 错误码说明

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 1001 | 学员不存在 | 检查学员ID是否正确 |
| 1002 | 预约不存在 | 检查预约ID是否正确 |
| 1003 | 时间段冲突 | 选择其他时间段或修改为1v多课程 |
| 1004 | 剩余课程不足 | 提醒学员续费或查看剩余课程数 |
| 1005 | 重复签到 | 检查是否已经签到过 |
| 1006 | 参数格式错误 | 检查请求参数格式是否正确 |
| 1007 | 日期无效 | 检查日期格式是否为YYYY-MM-DD |
| 1008 | 时间段无效 | 检查时间段是否在营业时间内 |

## 7. 接口调用示例

### 7.1 使用curl调用

```bash
# 获取学员列表
curl -X GET "http://localhost:8000/api/students?page=1&size=10"

# 创建学员
curl -X POST "http://localhost:8000/api/students" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试学员",
    "learning_item": "蛙泳",
    "package_type": "1v1",
    "total_lessons": 10,
    "price": 200,
    "venue_share": 120
  }'

# 创建预约
curl -X POST "http://localhost:8000/api/appointments" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "1",
    "appointment_date": "2024-12-01",
    "time_slot": "08:00"
  }'

# 学员签到
curl -X POST "http://localhost:8000/api/attendance/checkin" \
  -H "Content-Type: application/json" \
  -d '{
    "appointment_id": "1",
    "student_id": "1"
  }'
```

### 7.2 使用JavaScript调用

```javascript
// 获取学员列表
async function getStudents() {
  try {
    const response = await fetch('/api/students?page=1&size=10')
    const data = await response.json()
    console.log('学员列表:', data.data.items)
  } catch (error) {
    console.error('获取失败:', error)
  }
}

// 创建学员
async function createStudent(studentData) {
  try {
    const response = await fetch('/api/students', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(studentData)
    })
    const data = await response.json()
    console.log('创建成功:', data.data)
  } catch (error) {
    console.error('创建失败:', error)
  }
}

// 学员签到
async function checkIn(appointmentId, studentId) {
  try {
    const response = await fetch('/api/attendance/checkin', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        appointment_id: appointmentId,
        student_id: studentId
      })
    })
    const data = await response.json()
    console.log('签到成功:', data.data)
  } catch (error) {
    console.error('签到失败:', error)
  }
}
```

## 8. 接口测试

### 8.1 Postman集合

可以导入以下Postman集合进行接口测试：

```json
{
  "info": {
    "name": "Easy Book API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8000/api"
    }
  ],
  "item": [
    {
      "name": "学员管理",
      "item": [
        {
          "name": "获取学员列表",
          "request": {
            "method": "GET",
            "header": [],
            "url": {
              "raw": "{{baseUrl}}/students?page=1&size=10",
              "host": ["{{baseUrl}}"],
              "path": ["students"],
              "query": [
                {"key": "page", "value": "1"},
                {"key": "size", "value": "10"}
              ]
            }
          }
        }
      ]
    }
  ]
}
```

### 8.2 自动化测试

```python
# 使用pytest进行API测试
import pytest
import requests

BASE_URL = "http://localhost:8000/api"

class TestStudentAPI:
    def test_get_students(self):
        response = requests.get(f"{BASE_URL}/students")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]
    
    def test_create_student(self):
        student_data = {
            "name": "测试学员",
            "learning_item": "蛙泳",
            "package_type": "1v1",
            "total_lessons": 10,
            "price": 200,
            "venue_share": 120
        }
        
        response = requests.post(f"{BASE_URL}/students", json=student_data)
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 201
        assert data["data"]["name"] == "测试学员"
```

---

*Easy Book - 泳课学员管理系统 API接口文档*