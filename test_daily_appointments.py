#!/usr/bin/env python3
import asyncio
import sys
import os

# 添加backend目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api_server.mongo_database import get_database

async def test_daily_appointments():
    db = get_database()
    await db.connect()

    print('=== 测试 get_daily_appointments 方法 ===')
    result = await db.get_daily_appointments('2025-12-06')
    print(f'Result: {result}')
    print(f'Date: {result.get("date")}')
    print(f'Slots count: {len(result.get("slots", []))}')
    for slot in result.get('slots', []):
        print(f'  Slot: {slot.get("time")} - Students: {len(slot.get("students", []))}')

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(test_daily_appointments())