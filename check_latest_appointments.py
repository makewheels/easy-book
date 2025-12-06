#!/usr/bin/env python3
import asyncio
import sys
import os

# 添加backend目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api_server.mongo_database import get_database
from datetime import datetime

async def check_latest_appointments():
    db = get_database()
    await db.connect()

    print('=== 检查最新的预约数据 ===')

    # 查询最近10分钟的所有预约
    from datetime import timedelta
    recent_time = datetime.now() - timedelta(minutes=10)

    appointments = []
    async for apt in db.db.appointments.find({
        'create_time': {'$gte': recent_time}
    }).sort('create_time', -1):
        appointments.append(apt)
        print(f'预约ID: {apt["_id"]}')
        print(f'  学员: {apt.get("student_id")}')
        print(f'  开始时间: {apt.get("start_time")}')
        print(f'  状态: {apt.get("status")}')
        print(f'  创建时间: {apt.get("create_time")}')
        print('---')

    print(f'\n总共找到 {len(appointments)} 个最近预约')

    # 查询10:00的所有预约
    print('\n=== 查询所有10:00的预约 ===')
    ten_oclock_appointments = []
    async for apt in db.db.appointments.find({
        'start_time': {
            '$gte': datetime.strptime('2025-12-06 10:00:00', '%Y-%m-%d %H:%M:%S'),
            '$lt': datetime.strptime('2025-12-06 10:01:00', '%Y-%m-%d %H:%M:%S')
        }
    }):
        ten_oclock_appointments.append(apt)
        print(f'预约ID: {apt["_id"]}')
        print(f'  学员: {apt.get("student_id")}')
        print(f'  状态: {apt.get("status")}')
        print(f'  创建时间: {apt.get("create_time")}')
        print('---')

    print(f'\n总共找到 {len(ten_oclock_appointments)} 个10:00的预约')

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_latest_appointments())