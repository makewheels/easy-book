#!/usr/bin/env python3
import asyncio
import sys
import os
from datetime import date

# 添加backend目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api_server.services.appointment import AppointmentService

async def test_api_flow():
    print('=== 模拟API调用流程 ===')

    # 1. 模拟API收到的date对象
    target_date = date.fromisoformat('2025-12-06')
    print(f'API收到的date对象: {target_date} (type: {type(target_date)})')

    # 2. 转换为字符串
    date_str = str(target_date)
    print(f'转换为字符串: {date_str}')

    # 3. 调用AppointmentService
    daily_data = await AppointmentService.get_daily_appointments(date_str)
    print(f'AppointmentService返回: {type(daily_data)}')
    print(f'slots数量: {len(daily_data.get("slots", []))}')

    # 4. 模拟API返回
    api_response = {
        "code": 200,
        "message": "获取成功",
        "data": daily_data
    }
    print(f'API响应slots数量: {len(api_response["data"].get("slots", []))}')

if __name__ == "__main__":
    asyncio.run(test_api_flow())