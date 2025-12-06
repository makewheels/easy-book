#!/usr/bin/env python3
import asyncio
import sys
import os

# 添加backend目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api_server.mongo_database import get_database

async def check_today_appointments():
    db = get_database()
    await db.connect()

    # 获取所有今天(2025-12-06)的预约
    from datetime import datetime, timedelta

    start_date = datetime.strptime("2025-12-06", "%Y-%m-%d")
    end_date = datetime.strptime(f"2025-12-06T23:59:59", "%Y-%m-%dT%H:%M:%S")

    print(f"Querying appointments from {start_date} to {end_date}")

    appointments = []
    async for appointment in db.db.appointments.find({
        "start_time": {
            "$gte": start_date,
            "$lte": end_date
        }
    }):
        appointments.append(appointment)
        print(f"Found appointment:")
        print(f"  ID: {appointment['_id']}")
        print(f"  Student ID: {appointment.get('student_id')}")
        print(f"  Start time: {appointment['start_time']} (type: {type(appointment['start_time'])})")
        print(f"  Status: {appointment.get('status')}")
        print(f"  Create time: {appointment.get('create_time')}")
        print("---")

    print(f"\nTotal appointments found: {len(appointments)}")

    # 查询最近10分钟创建的预约
    from datetime import datetime, timedelta
    recent_time = datetime.now() - timedelta(minutes=10)
    print(f"\n\nRecent appointments (last 10 minutes, since {recent_time}):")
    recent_appointments = []
    async for appointment in db.db.appointments.find({
        "create_time": {"$gte": recent_time}
    }).sort("create_time", -1):
        recent_appointments.append(appointment)
        print(f"ID: {appointment['_id']}")
        print(f"  Student: {appointment.get('student_id')}")
        print(f"  Start: {appointment.get('start_time')}")
        print(f"  Status: {appointment.get('status')}")
        print(f"  Create: {appointment.get('create_time')}")
        print("---")

    if not recent_appointments:
        print("No recent appointments found in the last 10 minutes")

    # 查询王芳的预约
    print(f"\n\n王芳的预约 (student_id: 692f0f558a3ca1ece733a064):")
    wangfang_appointments = []
    async for appointment in db.db.appointments.find({
        "student_id": "692f0f558a3ca1ece733a064"
    }).sort("create_time", -1):
        wangfang_appointments.append(appointment)
        print(f"ID: {appointment['_id']}")
        print(f"  Start: {appointment.get('start_time')}")
        print(f"  Status: {appointment.get('status')}")
        print(f"  Create: {appointment.get('create_time')}")
        print("---")

    # 查询所有学员
    print(f"\n\n所有学员:")
    all_students = []
    async for student in db.db.students.find():
        all_students.append(student)
        print(f"ID: {student['_id']}, Name: {student.get('name')}, Remaining: {student.get('remaining_lessons', 0)}")

    print(f"\n总共 {len(all_students)} 个学员")

    # 详细检查三个保留学员的信息
    keep_student_ids = [
        "692f0f558a3ca1ece733a064",  # 马文华
        "692bd06358ba9900a7ac5b67",  # 许志玲
        "692c0d612e3567ee406e053a"   # 李文华
    ]

    print(f"\n\n保留学员详细信息:")
    for student_id in keep_student_ids:
        student = await db.get_student(student_id)
        if student:
            print(f"  {student.get('name')}:")
            print(f"    ID: {student_id}")
            print(f"    剩余课程: {student.get('remaining_lessons', 0)}")
            print(f"    总课程: {student.get('total_lessons', 0)}")
            print(f"    已上课: {student.get('attended_lessons', 0)}")
            print("---")

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_today_appointments())