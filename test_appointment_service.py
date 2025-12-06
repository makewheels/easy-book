#!/usr/bin/env python3
import asyncio
import sys
import os

# 添加backend目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api_server.services.appointment import AppointmentService

async def test_appointment_service():
    print('=== 测试 AppointmentService.get_daily_appointments 方法 ===')
    result = await AppointmentService.get_daily_appointments('2025-12-06')
    print(f'Result type: {type(result)}')
    print(f'Result: {result}')
    if isinstance(result, list):
        print(f'Result length: {len(result)}')
    elif isinstance(result, dict):
        print(f'Result keys: {result.keys()}')
        print(f'Slots count: {len(result.get("slots", []))}')

if __name__ == "__main__":
    asyncio.run(test_appointment_service())