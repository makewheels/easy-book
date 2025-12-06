#!/usr/bin/env python3
import asyncio
import sys
import os

# 添加backend目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api_server.mongo_database import get_database
from datetime import datetime

async def check_appointment_times():
    db = get_database()
    await db.connect()

    print('=== 检查10:00预约的详细信息 ===')
    appointment = await db.db.appointments.find_one({'_id': '6934116d9182cdb280e3c5a3'})
    if appointment:
        print(f'Appointment ID: {appointment["_id"]}')
        print(f'Start Time: {appointment["start_time"]} (type: {type(appointment["start_time"])})')
        print(f'Start Time ISO: {appointment["start_time"].isoformat()}')
        print(f'Start Time Hour: {appointment["start_time"].hour}')
        print(f'Start Time Minute: {appointment["start_time"].minute}')
        print(f'Status: {appointment.get("status")}')
    else:
        print('Appointment not found')

    print('\n=== 检查数据库查询范围 ===')
    start_date = datetime.strptime('2025-12-06', '%Y-%m-%d')
    end_date = datetime.strptime('2025-12-06T23:59:59', '%Y-%m-%dT%H:%M:%S')
    print(f'Query start: {start_date}')
    print(f'Query end: {end_date}')

    print('\n=== 测试查询 ===')
    count = 0
    async for apt in db.db.appointments.find({
        'start_time': {
            '$gte': start_date,
            '$lte': end_date
        },
        'status': { '$ne': 'cancel' }
    }):
        count += 1
        print(f'Found {count}: {apt["start_time"]} - {apt["status"]}')

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_appointment_times())