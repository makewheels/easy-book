#!/usr/bin/env python3
"""
测试预约API的新时间格式
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

import requests

API_BASE = "http://localhost:8004/api"

async def test_new_time_format():
    """测试新的时间格式API"""
    print("开始测试新的预约时间格式...")

    # 1. 创建测试学员
    print("\n步骤1: 创建测试学员...")
    student_data = {
        "name": "测试新时间格式学员",
        "learning_item": "游泳测试",
        "package_type": "1v1",
        "total_lessons": 5,
        "price": 500,
        "venue_share": 150,
        "note": "测试新的时间格式API"
    }

    try:
        response = requests.post(f"{API_BASE}/students/", json=student_data)
        if response.status_code == 200:
            student = response.json()
            student_id = student.get("_id")
            print(f"学员创建成功: {student['name']} (ID: {student_id})")
        else:
            print(f"学员创建失败: {response.text}")
            return False
    except Exception as e:
        print(f"学员创建异常: {e}")
        return False

    # 2. 测试不同时长的预约创建
    test_cases = [
        {
            "name": "1小时预约",
            "start_time": "2025-12-07T09:00:00",
            "duration": 60,
            "expected_end": "2025-12-07T10:00:00"
        },
        {
            "name": "1.5小时预约",
            "start_time": "2025-12-07T14:00:00",
            "duration": 90,
            "expected_end": "2025-12-07T15:30:00"
        },
        {
            "name": "2小时预约",
            "start_time": "2025-12-07T16:00:00",
            "duration": 120,
            "expected_end": "2025-12-07T18:00:00"
        }
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n步骤{i+1}: 测试{case['name']}...")

        appointment_data = {
            "student_id": student_id,
            "start_time": case["start_time"],
            "duration": case["duration"]
        }

        try:
            response = requests.post(f"{API_BASE}/appointments/", json=appointment_data)
            if response.status_code == 200:
                appointment = response.json()
                appointment_id = appointment.get("data", {}).get("id")
                actual_end = appointment.get("data", {}).get("end_time")

                print(f"{case['name']}创建成功")
                print(f"   开始时间: {appointment['data']['start_time']}")
                print(f"   预期结束: {case['expected_end']}")
                print(f"   实际结束: {actual_end}")
                print(f"   时长: {appointment['data']['duration']}分钟")
                print(f"   状态: {appointment['data']['status']}")

                # 验证结束时间计算是否正确
                if actual_end == case["expected_end"]:
                    print(f"   结束时间计算正确")
                else:
                    print(f"   结束时间计算错误")

            elif response.status_code == 400:
                error_msg = response.json().get("message", "未知错误")
                print(f"{case['name']}创建失败: {error_msg}")

            else:
                print(f"{case['name']}创建失败: HTTP {response.status_code}")

        except Exception as e:
            print(f"{case['name']}创建异常: {e}")

    # 3. 测试时间冲突检测
    print(f"\n步骤4: 测试时间冲突检测...")
    conflict_data = {
        "student_id": student_id,
        "start_time": "2025-12-07T09:00:00",  # 与第一个预约冲突
        "duration": 60
    }

    try:
        response = requests.post(f"{API_BASE}/appointments/", json=conflict_data)
        if response.status_code == 400:
            print("时间冲突检测正常工作")
        else:
            print(f"时间冲突检测失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"时间冲突检测异常: {e}")

    # 4. 测试学员预约查询
    print(f"\n步骤5: 测试学员预约查询...")
    try:
        response = requests.get(f"{API_BASE}/appointments/student/{student_id}")
        if response.status_code == 200:
            appointments = response.json()
            print(f"学员预约查询成功，共 {len(appointments)} 个预约")
            for apt in appointments:
                start_time = apt.get('start_time', '')[:16]  # 只显示日期时间部分
                duration = apt.get('duration', 0)
                status = apt.get('status', '')
                print(f"   - {start_time} | {duration}分钟 | {status}")
        else:
            print(f"学员预约查询失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"学员预约查询异常: {e}")

    # 5. 测试日历API
    print(f"\n步骤6: 测试日历API...")
    try:
        response = requests.get(f"{API_BASE}/appointments/daily/2025-12-07")
        if response.status_code == 200:
            daily_data = response.json()
            if daily_data.get("code") == 200:
                print(f"日历API查询成功")
                print(f"   日期: {daily_data['data']['date']}")
                print(f"   星期: {daily_data['data']['weekday']}")
                print(f"   时间段数量: {len(daily_data['data']['slots'])}")
                for slot in daily_data['data']['slots']:
                    time = slot.get('time', '')
                    students = slot.get('students', [])
                    print(f"   - {time}: {len(students)} 个学员")
            else:
                print(f"日历API返回错误: {daily_data.get('message')}")
        else:
            print(f"日历API查询失败: HTTP {response.status_code}")
    except Exception as e:
        print(f"日历API查询异常: {e}")

    print("\n新时间格式测试完成!")
    return True

if __name__ == "__main__":
    asyncio.run(test_new_time_format())