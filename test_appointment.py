#!/usr/bin/env python3
"""
测试预约创建 - 模拟前端API调用格式
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from datetime import datetime
from api_server.services.appointment import AppointmentService

async def test_appointment_api_format():
    """测试前端API格式的预约创建"""
    try:
        # 模拟前端发送的数据格式
        appointment_data = {
            "student_id": "692bd06358ba9900a7ac5b67",
            "start_time": "2025-12-07T14:00:00",
            "duration_in_minutes": 60
        }

        print("开始创建预约（前端API格式）...")
        print(f"预约数据: {appointment_data}")

        # 验证必需字段
        required_fields = ["student_id", "start_time", "duration_in_minutes"]
        for field in required_fields:
            if field not in appointment_data:
                raise ValueError(f"缺少必需字段: {field}")

        # 计算结束时间
        start_time = appointment_data["start_time"]
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

        duration_in_minutes = appointment_data["duration_in_minutes"]
        end_time = start_time + timedelta(minutes=duration_in_minutes)

        # 构建预约数据
        appointment_data_internal = {
            "student_id": appointment_data["student_id"],
            "start_time": start_time,
            "end_time": end_time
        }

        print(f"内部预约数据: {appointment_data_internal}")

        appointment = await AppointmentService.create_appointment(appointment_data_internal)
        print(f"预约创建成功: {appointment}")

    except Exception as e:
        print(f"预约创建失败: {e}")
        import traceback
        traceback.print_exc()

async def test_appointment():
    """测试直接格式"""
    try:
        appointment_data = {
            "student_id": "692bd06358ba9900a7ac5b67",
            "start_time": datetime(2025, 12, 6, 14, 0, 0),
            "end_time": datetime(2025, 12, 6, 15, 0, 0)
        }

        print("开始创建预约...")
        print(f"预约数据: {appointment_data}")

        appointment = await AppointmentService.create_appointment(appointment_data)
        print(f"预约创建成功: {appointment}")

    except Exception as e:
        print(f"预约创建失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from datetime import timedelta
    asyncio.run(test_appointment_api_format())