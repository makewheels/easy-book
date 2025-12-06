#!/usr/bin/env python3
import asyncio
import sys
import os

# 添加backend目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api_server.mongo_database import get_database

async def check_attendances():
    db = get_database()
    await db.connect()

    print('=== 检查attendances数据 ===')

    # 统计attendances总数
    total_count = await db.db.attendances.count_documents({})
    print(f'总考勤记录数: {total_count}')

    if total_count > 0:
        print('\n最近的考勤记录:')
        attendances = []
        async for att in db.db.attendances.find({}).sort('create_time', -1).limit(5):
            attendances.append(att)
            print(f'  ID: {att["_id"]}')
            print(f'  学员: {att.get("student_id")}')
            print(f'  预约: {att.get("appointment_id")}')
            print(f'  日期: {att.get("attendance_date")}')
            print(f'  时间: {att.get("time_slot")}')
            print(f'  状态: {att.get("status")}')
            print(f'  课程变化: {att.get("lessons_before")} → {att.get("lessons_after")}')
            print('---')
    else:
        print('数据库中没有任何考勤记录')

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_attendances())