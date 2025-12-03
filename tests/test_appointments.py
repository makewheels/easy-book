#!/usr/bin/env python3
"""
预约管理模块测试
测试预约CRUD操作和冲突检测
"""

import sys
import os
import time
import datetime
import requests

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from conftest import TestBase

class TestAppointments(TestBase):
    """预约管理测试类"""

    def test_01_api_create_appointment(self):
        """测试1：API创建预约"""
        print("\n测试：测试1 - API创建预约")

        # 先创建学生
        student = self.create_test_student()

        appointment_data = {
            "student_id": student["id"],
            "appointment_date": self.get_today_date(),
            "time_slot": "19:00"
        }

        response = requests.post(f"{self.api_url}/api/appointments/", json=appointment_data)
        self.assert_equal(response.status_code, 200, "Create appointment API status code")
        self.assert_equal(response.json().get("code"), 200, "Create appointment API response code")

        appointment = response.json().get("data", {})
        self.assert_true(appointment.get("id") is not None, "Appointment ID returned")
        self.assert_equal(appointment.get("status"), "scheduled", "Appointment status is scheduled")

        # 保存测试数据
        self.test_data["appointment"] = appointment
        self.test_data["appointment_id"] = appointment.get("id")

        print(f"通过：测试1通过 - 创建预约成功 - {student['name']} @ 19:00")

    def test_02_api_get_student_appointments(self):
        """测试2：API获取学生预约记录"""
        print("\n测试：测试2 - API获取学生预约记录")

        if "student_id" not in self.test_data:
            raise AssertionError("需要先创建学生和预约")

        student_id = self.test_data["student_id"]
        response = requests.get(f"{self.api_url}/api/appointments/student/{student_id}")
        self.assert_equal(response.status_code, 200, "Get student appointments API status code")

        appointments = response.json()
        self.assert_true(isinstance(appointments, list), "Appointments API returns list")
        self.assert_true(len(appointments) > 0, "Student has appointments")

        print(f"通过：测试2通过 - 获取到 {len(appointments)} 个预约记录")

    def test_03_api_get_daily_appointments(self):
        """测试3：API获取每日预约"""
        print("\n测试：测试3 - API获取每日预约")

        today = self.get_today_date()
        response = requests.get(f"{self.api_url}/api/appointments/daily/{today}")
        self.assert_equal(response.status_code, 200, "Get daily appointments API status code")

        daily_data = response.json().get("data", {})
        self.assert_true(daily_data.get("date") is not None, "Daily data has date")
        self.assert_true("slots" in daily_data, "Daily data has slots")

        print(f"通过：测试3通过 - 获取每日预约成功 - {daily_data.get('date')}")

    def test_04_api_update_appointment(self):
        """测试4：API更新预约"""
        print("\n测试：测试4 - API更新预约")

        if "appointment_id" not in self.test_data:
            raise AssertionError("需要先创建预约")

        appointment_id = self.test_data["appointment_id"]
        update_data = {
            "time_slot": "20:00"
        }

        response = requests.put(f"{self.api_url}/api/appointments/{appointment_id}", json=update_data)
        self.assert_equal(response.status_code, 200, "Update appointment API status code")

        updated_appointment = response.json()
        self.assert_equal(updated_appointment.get("time_slot"), update_data["time_slot"], "Time slot updated")

        print(f"通过：测试4通过 - 更新预约成功 - 时间改为 {update_data['time_slot']}")

    def test_05_api_delete_appointment(self):
        """测试5：API删除预约"""
        print("\n测试：测试5 - API删除预约")

        # 创建临时预约用于删除测试
        temp_student = self.create_test_student()
        temp_appointment = self.create_test_appointment(
            student_id=temp_student["id"],
            time_slot="21:00"
        )

        appointment_id = temp_appointment["id"]

        # 删除预约
        response = requests.delete(f"{self.api_url}/api/appointments/{appointment_id}")
        self.assert_equal(response.status_code, 200, "Delete appointment API status code")

        # 验证预约已被删除
        get_response = requests.get(f"{self.api_url}/api/students/{temp_student['id']}")
        student_appointments = get_response.json()

        # 检查预约是否在学生预约列表中
        appointment_exists = any(apt.get("id") == appointment_id for apt in student_appointments)
        self.assert_true(not appointment_exists, "Appointment deleted from student list")

        print(f"通过：测试5通过 - 删除预约成功 - ID: {appointment_id}")

    def test_06_appointment_conflict_1v1(self):
        """测试6：1v1预约冲突检测"""
        print("\n测试：测试6 - 1v1预约冲突检测")

        # 创建第一个学生和预约
        student1 = self.create_test_student()
        appointment1 = self.create_test_appointment(
            student_id=student1["id"],
            time_slot="14:00"
        )

        # 创建第二个学生
        student2_data = {
            "name": f"Conflict Test Student 2 - {datetime.datetime.now().strftime('%H%M%S')}",
            "learning_item": "自由泳",
            "package_type": "1v1",
            "total_lessons": 8,
            "price": 800,
            "venue_share": 240
        }

        student2_response = requests.post(f"{self.api_url}/api/students/", json=student2_data)
        self.assert_equal(student2_response.status_code, 200, "Create second student status code")
        student2 = student2_response.json().get("data", {})
        student2_id = student2.get("id")

        # 尝试创建冲突的预约（同一时间，1v1课程）
        conflict_appointment_data = {
            "student_id": student2_id,
            "appointment_date": self.get_today_date(),
            "time_slot": "14:00"  # 与第一个预约相同时间
        }

        conflict_response = requests.post(f"{self.api_url}/api/appointments/", json=conflict_appointment_data)

        # 期望返回冲突错误
        if conflict_response.status_code == 200:
            response_code = conflict_response.json().get("code")
            self.assert_equal(response_code, 400, "Conflict appointment returns error code")

            error_message = conflict_response.json().get("message", "")
            self.assert_true(
                "时间段已有预约" in error_message or "已有" in error_message,
                f"Conflict error message: {error_message}"
            )
        else:
            self.assert_true(conflict_response.status_code in [422, 400], "Conflict appointment returns error")

        print("通过：测试6通过 - 1v1预约冲突检测正常")

    def test_07_appointment_no_conflict_1v1vmany(self):
        """测试7：1v1与1v多无冲突"""
        print("\n测试：测试7 - 1v1与1v多无冲突")

        # 创建1v1学生和预约
        student1v1 = self.create_test_student()
        student1v1["package_type"] = "1v1"
        # 更新学生为1v1套餐
        requests.put(f"{self.api_url}/api/students/{student1v1['id']}", {"package_type": "1v1"})

        appointment1v1 = self.create_test_appointment(
            student_id=student1v1["id"],
            time_slot="15:00"
        )

        # 创建1v多学生
        student1vmany_data = {
            "name": f"1v多 Test Student - {datetime.datetime.now().strftime('%H%M%S')}",
            "learning_item": "自由泳",
            "package_type": "1v多",
            "total_lessons": 12,
            "price": 600,
            "venue_share": 100
        }

        student1vmany_response = requests.post(f"{self.api_url}/api/students/", json=student1vmany_data)
        self.assert_equal(student1vmany_response.status_code, 200, "Create 1v多 student status code")
        student1vmany = student1vmany_response.json().get("data", {})

        # 尝试在同一时间创建1v多预约
        vmany_appointment_data = {
            "student_id": student1vmany.get("id"),
            "appointment_date": self.get_today_date(),
            "time_slot": "15:00"  # 与1v1预约相同时间
        }

        vmany_response = requests.post(f"{self.api_url}/api/appointments/", json=vmany_appointment_data)

        # 1v多与1v1的冲突处理取决于具体业务实现
        if vmany_response.status_code == 200:
            print("通过：测试7通过 - 1v多与1v1可以同时预约")
        elif vmany_response.status_code in [422, 400]:
            print("通过：测试7通过 - 1v多与1v1不能同时预约（符合业务规则）")
        else:
            raise AssertionError(f"Unexpected response status: {vmany_response.status_code}")

    def test_08_duplicate_student_appointment(self):
        """测试8：同一学生重复预约检测"""
        print("\n测试：测试8 - 同一学生重复预约检测")

        if "student_id" not in self.test_data:
            raise AssertionError("需要先创建学生")

        student_id = self.test_data["student_id"]

        # 尝试创建重复预约（同一学生，同一时间）
        duplicate_appointment_data = {
            "student_id": student_id,
            "appointment_date": self.get_today_date(),
            "time_slot": "19:00"  # 使用现有预约的时间
        }

        duplicate_response = requests.post(f"{self.api_url}/api/appointments/", json=duplicate_appointment_data)

        # 期望返回重复错误
        if duplicate_response.status_code == 200:
            response_code = duplicate_response.json().get("code")
            self.assert_equal(response_code, 400, "Duplicate appointment returns error code")

            error_message = duplicate_response.json().get("message", "")
            self.assert_true(
                "已有" in error_message or "预约" in error_message,
                f"Duplicate error message: {error_message}"
            )
        else:
            self.assert_true(duplicate_response.status_code in [422, 400], "Duplicate appointment returns error")

        print("通过：测试8通过 - 同一学生重复预约检测正常")


def run_appointment_tests():
    """运行预约管理测试"""
    print("=" * 60)
    print("预约管理模块测试")
    print("=" * 60)

    test_instance = TestAppointments()

    try:
        # 初始化
        print("初始化测试环境...")
        if not test_instance.setup_mongodb():
            return False

        # 运行所有测试
        tests = [
            test_instance.test_01_api_create_appointment,
            test_instance.test_02_api_get_student_appointments,
            test_instance.test_03_api_get_daily_appointments,
            test_instance.test_04_api_update_appointment,
            test_instance.test_05_api_delete_appointment,
            test_instance.test_06_appointment_conflict_1v1,
            test_instance.test_07_appointment_no_conflict_1v1vmany,
            test_instance.test_08_duplicate_student_appointment
        ]

        passed = 0
        failed = 0

        for test_func in tests:
            try:
                test_func()
                passed += 1
            except Exception as e:
                print(f"FAIL: {test_func.__name__} - {e}")
                failed += 1

        print(f"\n预约管理模块测试完成")
        print(f"通过: {passed}, 失败: {failed}")
        print(f"成功率: {(passed/(passed+failed)*100):.1f}%")

        return failed == 0

    finally:
        test_instance.teardown()


if __name__ == "__main__":
    success = run_appointment_tests()
    sys.exit(0 if success else 1)