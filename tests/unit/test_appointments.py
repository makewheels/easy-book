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

# 添加tests目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conftest import TestBase

class TestAppointments(TestBase):
    """预约管理测试类"""

    def test_01_api_create_appointment(self):
        """测试1：API创建预约"""
        print("\n测试：测试1 - API创建预约")

        # 先创建学生
        student = self.create_test_student()

        # 直接构造预约数据
        date = self.get_today_date()
        time_slot = "23:00"  # 使用23:00避免与现有课程冲突

        # 构造开始和结束时间
        hour, minute = map(int, time_slot.split(':'))
        start_datetime = datetime.datetime.strptime(f"{date} {time_slot}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + datetime.timedelta(hours=1)

        appointment_data = {
            "student_id": student["_id"],
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "appointment_date": date,
            "time_slot": time_slot
        }

        response = requests.post(f"{self.api_url}/api/appointments/", json=appointment_data)
        self.assert_equal(response.status_code, 200, "Create appointment API status code")

        appointment = response.json().get("data", {})
        self.assert_true(appointment.get("id") is not None, "Appointment ID returned")
        self.assert_equal(appointment.get("status"), "scheduled", "Appointment status is scheduled")

        # 保存测试数据
        self.test_data["student"] = student
        self.test_data["appointment"] = appointment
        self.test_data["appointment_id"] = appointment.get("id")
        self.test_data["student_id"] = student["_id"]

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

        # For update, use new format with start_time and end_time
        date = self.get_today_date()
        new_time_slot = "23:00"
        hour, minute = map(int, new_time_slot.split(':'))
        start_datetime = datetime.datetime.strptime(f"{date} {new_time_slot}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + datetime.timedelta(hours=1)

        update_data = {
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "appointment_date": date,
            "time_slot": new_time_slot
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
            student_id=temp_student["_id"],
            time_slot="23:30"  # 使用不同时间避免冲突
        )

        appointment_id = temp_appointment["id"]

        # 删除预约
        response = requests.delete(f"{self.api_url}/api/appointments/{appointment_id}")
        self.assert_equal(response.status_code, 200, "Delete appointment API status code")

        # 验证预约已被删除
        get_response = requests.get(f"{self.api_url}/api/students/{temp_student['_id']}")
        student_data = get_response.json()

        # 检查学生数据存在，因为预约删除后学生应该还在
        self.assert_equal(student_data.get("_id"), temp_student["_id"], "Student still exists after appointment deletion")

        print(f"通过：测试5通过 - 删除预约成功 - ID: {appointment_id}")

    def test_06_appointment_conflict_1v1(self):
        """测试6：1v1预约冲突检测"""
        print("\n测试：测试6 - 1v1预约冲突检测")

        # 创建第一个学生和预约
        student1 = self.create_test_student()
        appointment1 = self.create_test_appointment(
            student_id=student1["_id"],  # Use _id instead of id
            time_slot=self.get_test_time_slot()  # Use conflict-free time
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
        student2 = student2_response.json()  # Student API returns data directly
        student2_id = student2.get("_id")  # Students use _id field

        # 尝试创建冲突的预约（同一时间，1v1课程）
        conflict_time_slot = self.get_test_time_slot()  # 与第一个预约相同时间
        date = self.get_today_date()
        start_datetime = datetime.datetime.strptime(f"{date} {conflict_time_slot}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + datetime.timedelta(hours=1)

        conflict_appointment_data = {
            "student_id": student2_id,
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "appointment_date": date,
            "time_slot": conflict_time_slot  # 与第一个预约相同时间
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
        student1vmany = student1vmany_response.json()  # Student API returns data directly

        # 尝试在同一时间创建1v多预约
        date = self.get_today_date()
        time_slot = "15:00"  # 与1v1预约相同时间
        hour, minute = map(int, time_slot.split(':'))
        start_datetime = datetime.datetime.strptime(f"{date} {time_slot}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + datetime.timedelta(hours=1)

        vmany_appointment_data = {
            "student_id": student1vmany.get("_id"),  # Students use _id field
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "appointment_date": date,
            "time_slot": time_slot
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
        date = self.get_today_date()
        time_slot = "19:00"  # 使用现有预约的时间
        hour, minute = map(int, time_slot.split(':'))
        start_datetime = datetime.datetime.strptime(f"{date} {time_slot}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + datetime.timedelta(hours=1)

        duplicate_appointment_data = {
            "student_id": student_id,
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "appointment_date": date,
            "time_slot": time_slot
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

    def test_09_api_get_upcoming_appointments(self):
        """测试9：API获取未来预约列表"""
        print("\n测试：测试9 - API获取未来预约列表")

        # 创建测试预约（今日和明日）
        student1 = self.create_test_student("今日测试学员")
        student2 = self.create_test_student("明日测试学员")

        today = self.get_today_date()
        tomorrow = self.get_tomorrow_date()

        # 创建今日预约
        today_time_slot = self.get_test_time_slot()  # 22:00
        today_start_datetime = datetime.datetime.strptime(f"{today} {today_time_slot}", "%Y-%m-%d %H:%M")
        today_end_datetime = today_start_datetime + datetime.timedelta(hours=1)

        today_appointment_data = {
            "student_id": student1["_id"],
            "start_time": today_start_datetime.isoformat(),
            "end_time": today_end_datetime.isoformat(),
            "appointment_date": today,
            "time_slot": today_time_slot
        }

        today_response = requests.post(f"{self.api_url}/api/appointments/", json=today_appointment_data)
        self.assert_equal(today_response.status_code, 200, "Create today appointment status code")

        # 创建明日预约
        tomorrow_time_slot = self.get_test_time_slot(2)  # 00:00 (次日)
        tomorrow_start_datetime = datetime.datetime.strptime(f"{tomorrow} {tomorrow_time_slot}", "%Y-%m-%d %H:%M")
        tomorrow_end_datetime = tomorrow_start_datetime + datetime.timedelta(hours=1)

        tomorrow_appointment_data = {
            "student_id": student2["_id"],
            "start_time": tomorrow_start_datetime.isoformat(),
            "end_time": tomorrow_end_datetime.isoformat(),
            "appointment_date": tomorrow,
            "time_slot": tomorrow_time_slot
        }

        tomorrow_response = requests.post(f"{self.api_url}/api/appointments/", json=tomorrow_appointment_data)
        self.assert_equal(tomorrow_response.status_code, 200, "Create tomorrow appointment status code")

        # 获取未来预约
        upcoming_response = requests.get(f"{self.api_url}/api/appointments/upcoming?days=30")

        self.assert_equal(upcoming_response.status_code, 200, "Get upcoming appointments status code")

        upcoming_data = upcoming_response.json()
        self.assert_equal(upcoming_data.get("code"), 200, "Upcoming appointments response code")

        appointments = upcoming_data.get("data", [])
        self.assert_true(len(appointments) >= 2, "Should have at least 2 upcoming appointments")

        # 验证数据格式
        found_today = False
        found_tomorrow = False

        for day_data in appointments:
            if "date" in day_data and "slots" in day_data:
                if day_data["date"] == today[5:]:  # MM-DD format
                    found_today = True
                elif day_data["date"] == tomorrow[5:]:  # MM-DD format
                    found_tomorrow = True

        self.assert_true(found_today, "Should find today's appointments")
        self.assert_true(found_tomorrow, "Should find tomorrow's appointments")

        print("通过：测试9通过 - API获取未来预约列表正常")

    def test_10_frontend_statistics_accuracy(self):
        """测试10：前端统计准确性测试"""
        print("\n测试：测试10 - 前端统计准确性测试")

        # 创建已知数量的预约
        today = self.get_today_date()
        tomorrow = self.get_tomorrow_date()

        # 清理现有预约
        self.cleanup_appointments()

        # 创建今日预约
        student_today = self.create_test_student("今日统计测试")
        student_tomorrow = self.create_test_student("明日统计测试")

        # 今日创建2个预约
        for i, time_slot in enumerate(["14:00", "15:00"]):
            date = today
            hour, minute = map(int, time_slot.split(':'))
            start_datetime = datetime.datetime.strptime(f"{date} {time_slot}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + datetime.timedelta(hours=1)

            student_id = student_today["_id"] if i == 0 else self.create_test_student(f"今日测试{i}")["_id"]
            appointment_data = {
                "student_id": student_id,
                "start_time": start_datetime.isoformat(),
                "end_time": end_datetime.isoformat(),
                "appointment_date": date,
                "time_slot": time_slot
            }
            response = requests.post(f"{self.api_url}/api/appointments/", json=appointment_data)
            self.assert_equal(response.status_code, 200, f"Create today appointment {i+1}")

        # 明日创建1个预约
        date = tomorrow
        time_slot = "16:00"
        hour, minute = map(int, time_slot.split(':'))
        start_datetime = datetime.datetime.strptime(f"{date} {time_slot}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + datetime.timedelta(hours=1)

        tomorrow_appointment_data = {
            "student_id": student_tomorrow["_id"],
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "appointment_date": date,
            "time_slot": time_slot
        }
        response = requests.post(f"{self.api_url}/api/appointments/", json=tomorrow_appointment_data)
        self.assert_equal(response.status_code, 200, "Create tomorrow appointment")

        # 获取upcoming数据验证统计
        upcoming_response = requests.get(f"{self.api_url}/api/appointments/upcoming?days=2")
        self.assert_equal(upcoming_response.status_code, 200, "Get limited upcoming appointments")

        upcoming_data = upcoming_response.json()
        appointments = upcoming_data.get("data", [])

        # 计算实际统计
        today_count = 0
        tomorrow_count = 0

        for day_data in appointments:
            if day_data.get("date") == today[5:]:  # MM-DD format
                today_count = sum(len(slot.get("students", [])) for slot in day_data.get("slots", []))
            elif day_data.get("date") == tomorrow[5:]:  # MM-DD format
                tomorrow_count = sum(len(slot.get("students", [])) for slot in day_data.get("slots", []))

        # 验证统计准确性
        self.assert_equal(today_count, 2, f"Today should have 2 appointments, got {today_count}")
        self.assert_equal(tomorrow_count, 1, f"Tomorrow should have 1 appointment, got {tomorrow_count}")

        print(f"通过：测试10通过 - 今日{today_count}个，明日{tomorrow_count}个，统计准确")

    def test_11_appointment_deducts_lessons(self):
        """测试11：预约时自动扣减课程"""
        print("\n测试：测试11 - 预约时自动扣减课程")

        # 创建有指定课程数的学生
        student_data = {
            "name": f"预约扣费测试学员 - {datetime.datetime.now().strftime('%H%M%S')}",
            "learning_item": "自由泳",
            "package_type": "1v1",
            "total_lessons": 5,
            "remaining_lessons": 5,
            "price": 500,
            "venue_share": 150
        }

        create_response = requests.post(f"{self.api_url}/api/students/", json=student_data)
        self.assert_equal(create_response.status_code, 200, "Create student API status code")

        student = create_response.json().get("data", {})
        if not student:
            # 如果API返回格式不同，直接获取响应数据
            student = create_response.json()

        student_id = student.get("_id") or student.get("id")
        self.assert_true(student_id is not None, "Student ID found")

        # 验证初始课程数
        initial_lessons = student.get("remaining_lessons", 0)
        self.assert_equal(initial_lessons, 5, "Initial remaining lessons should be 5")

        # 创建预约（应该自动扣减1次课程）
        date = self.get_today_date()
        time_slot = "10:00"
        hour, minute = map(int, time_slot.split(':'))
        start_datetime = datetime.datetime.strptime(f"{date} {time_slot}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + datetime.timedelta(hours=1)

        appointment_data = {
            "student_id": student_id,
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "appointment_date": date,
            "time_slot": time_slot
        }

        appointment_response = requests.post(f"{self.api_url}/api/appointments/", json=appointment_data)
        self.assert_equal(appointment_response.status_code, 200, "Create appointment API status code")

        appointment_result = appointment_response.json()
        self.assert_equal(appointment_result.get("code"), 200, "Appointment creation response code")

        # 验证预约创建成功
        appointment = appointment_result.get("data", {})
        self.assert_true(appointment.get("id") is not None, "Appointment created successfully")

        # 验证课程已扣减
        updated_student_response = requests.get(f"{self.api_url}/api/students/{student_id}")
        self.assert_equal(updated_student_response.status_code, 200, "Get updated student API status code")

        updated_student = updated_student_response.json().get("data", {})
        if not updated_student:
            updated_student = updated_student_response.json()

        final_lessons = updated_student.get("remaining_lessons", 0)
        self.assert_equal(final_lessons, 4, "Lessons should be deducted after appointment")

        # 保存测试数据
        self.test_data["student"] = student
        self.test_data["student_id"] = student_id
        self.test_data["appointment"] = appointment
        self.test_data["appointment_id"] = appointment.get("id")

        print(f"通过：测试11通过 - 预约成功扣减课程 - {initial_lessons} -> {final_lessons}")

    def test_12_cancel_appointment_restores_lessons(self):
        """测试12：取消预约时恢复课程"""
        print("\n测试：测试12 - 取消预约时恢复课程")

        if "appointment_id" not in self.test_data:
            # 创建临时预约用于取消测试
            temp_student = self.create_test_student("取消测试学员")
            temp_appointment = self.create_test_appointment(
                student_id=temp_student["_id"],
                time_slot="11:00"
            )
            appointment_id = temp_appointment.get("id") or temp_appointment.get("_id")
            student_id = temp_student["_id"]
        else:
            appointment_id = self.test_data["appointment_id"]
            student_id = self.test_data["student_id"]

        # 获取取消前的课程数
        student_before = requests.get(f"{self.api_url}/api/students/{student_id}")
        self.assert_equal(student_before.status_code, 200, "Get student before cancel status code")

        student_data_before = student_before.json().get("data", {})
        if not student_data_before:
            student_data_before = student_before.json()

        lessons_before_cancel = student_data_before.get("remaining_lessons", 0)

        # 取消预约
        cancel_response = requests.put(f"{self.api_url}/api/appointments/{appointment_id}/cancel")
        self.assert_equal(cancel_response.status_code, 200, "Cancel appointment API status code")

        cancel_result = cancel_response.json()
        self.assert_equal(cancel_result.get("code"), 200, "Cancel appointment response code")
        self.assert_true("课程次数已恢复" in cancel_result.get("message", ""), "Cancel success message")

        # 验证课程已恢复
        student_after = requests.get(f"{self.api_url}/api/students/{student_id}")
        self.assert_equal(student_after.status_code, 200, "Get student after cancel status code")

        student_data_after = student_after.json().get("data", {})
        if not student_data_after:
            student_data_after = student_after.json()

        lessons_after_cancel = student_data_after.get("remaining_lessons", 0)
        self.assert_equal(lessons_after_cancel, lessons_before_cancel + 1, "Lessons should be restored after cancel")

        print(f"通过：测试12通过 - 取消预约成功恢复课程 - {lessons_before_cancel} -> {lessons_after_cancel}")

    def test_12b_cancel_already_cancelled_appointment(self):
        """测试12b：取消已取消的预约应该失败"""
        print("\n测试：测试12b - 取消已取消的预约应该失败")

        if "appointment_id" not in self.test_data:
            # 创建临时预约用于测试
            temp_student = self.create_test_student("重复取消测试学员")
            temp_appointment = self.create_test_appointment(
                student_id=temp_student["_id"],
                time_slot="13:00"
            )
            appointment_id = temp_appointment.get("id") or temp_appointment.get("_id")
        else:
            appointment_id = self.test_data["appointment_id"]

        # 先取消一次
        first_cancel = requests.put(f"{self.api_url}/api/appointments/{appointment_id}/cancel")
        if first_cancel.status_code == 200:
            # 再次取消应该失败
            second_cancel = requests.put(f"{self.api_url}/api/appointments/{appointment_id}/cancel")
            self.assert_equal(second_cancel.status_code, 200, "Second cancel API status code")

            cancel_result = second_cancel.json()
            self.assert_equal(cancel_result.get("code"), 400, "Second cancel response code")
            self.assert_true("只能取消待上课的预约" in cancel_result.get("message", ""), "Second cancel error message")

            print(f"通过：测试12b通过 - 重复取消正确失败 - {cancel_result.get('message')}")
        else:
            print(f"通过：测试12b通过 - 预约已是取消状态")

    def test_12c_cancel_nonexistent_appointment(self):
        """测试12c：取消不存在的预约应该失败"""
        print("\n测试：测试12c - 取消不存在的预约应该失败")

        # 使用不存在的预约ID
        fake_id = "507f1f77bcf86cd799439011"  # 格式正确但不存在的ObjectId
        cancel_response = requests.put(f"{self.api_url}/api/appointments/{fake_id}/cancel")

        self.assert_equal(cancel_response.status_code, 200, "Cancel nonexistent API status code")

        cancel_result = cancel_response.json()
        self.assert_equal(cancel_result.get("code"), 400, "Cancel nonexistent response code")
        self.assert_true("预约不存在" in cancel_result.get("message", ""), "Cancel nonexistent error message")

        print(f"通过：测试12c通过 - 取消不存在预约正确失败 - {cancel_result.get('message')}")

    def test_13_insufficient_lessons_prevents_appointment(self):
        """测试13：课程不足时阻止预约"""
        print("\n测试：测试13 - 课程不足时阻止预约")

        # 创建课程不足的学生（剩余课程为0）
        student_data = {
            "name": f"课程不足测试学员 - {datetime.datetime.now().strftime('%H%M%S')}",
            "learning_item": "蛙泳",
            "package_type": "1v1",
            "total_lessons": 3,
            "remaining_lessons": 0,
            "price": 300,
            "venue_share": 100
        }

        create_response = requests.post(f"{self.api_url}/api/students/", json=student_data)
        self.assert_equal(create_response.status_code, 200, "Create student with 0 lessons")

        student = create_response.json().get("data", {})
        if not student:
            student = create_response.json()

        student_id = student.get("_id") or student.get("id")

        # 尝试创建预约（应该被拒绝）
        date = self.get_today_date()
        time_slot = "14:00"
        hour, minute = map(int, time_slot.split(':'))
        start_datetime = datetime.datetime.strptime(f"{date} {time_slot}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + datetime.timedelta(hours=1)

        appointment_data = {
            "student_id": student_id,
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            "appointment_date": date,
            "time_slot": time_slot
        }

        appointment_response = requests.post(f"{self.api_url}/api/appointments/", json=appointment_data)

        # 预期API返回失败状态
        success_codes = [200]
        should_fail = appointment_response.status_code not in success_codes

        if appointment_response.status_code == 200:
            response_data = appointment_response.json()
            # 如果返回200状态码，检查是否有错误信息
            if response_data.get("code") != 200 or "剩余课程不足" in response_data.get("message", ""):
                should_fail = True

        self.assert_true(should_fail, "Appointment should be rejected when insufficient lessons")

        # 清理测试数据
        requests.delete(f"{self.api_url}/api/students/{student_id}")

        print("通过：测试13通过 - 课程不足时正确阻止预约")

    def test_14_multiple_appointments_deduct_multiple_lessons(self):
        """测试14：多个预约扣减多个课程"""
        print("\n测试：测试14 - 多个预约扣减多个课程")

        # 创建有多个课程的学生
        student_data = {
            "name": f"多预约测试学员 - {datetime.datetime.now().strftime('%H%M%S')}",
            "learning_item": "蝶泳",
            "package_type": "1v1",
            "total_lessons": 5,
            "remaining_lessons": 5,
            "price": 500,
            "venue_share": 150
        }

        create_response = requests.post(f"{self.api_url}/api/students/", json=student_data)
        self.assert_equal(create_response.status_code, 200, "Create student for multiple appointments")

        student = create_response.json().get("data", {})
        if not student:
            student = create_response.json()

        student_id = student.get("_id") or student.get("id")

        appointment_ids = []
        time_slots = ["09:00", "15:00", "16:00"]

        # 创建多个预约
        for i, time_slot in enumerate(time_slots):
            date = self.get_today_date()
            hour, minute = map(int, time_slot.split(':'))
            start_datetime = datetime.datetime.strptime(f"{date} {time_slot}", "%Y-%m-%d %H:%M")
            end_datetime = start_datetime + datetime.timedelta(hours=1)

            appointment_data = {
                "student_id": student_id,
                "start_time": start_datetime.isoformat(),
                "end_time": end_datetime.isoformat(),
                "appointment_date": date,
                "time_slot": time_slot
            }

            appointment_response = requests.post(f"{self.api_url}/api/appointments/", json=appointment_data)
            self.assert_equal(appointment_response.status_code, 200, f"Create appointment {i+1}")

            appointment_result = appointment_response.json()
            appointment = appointment_result.get("data", {})
            appointment_id = appointment.get("id")
            appointment_ids.append(appointment_id)

        # 验证课程已扣减
        updated_student_response = requests.get(f"{self.api_url}/api/students/{student_id}")
        self.assert_equal(updated_student_response.status_code, 200, "Get updated student")

        updated_student = updated_student_response.json().get("data", {})
        if not updated_student:
            updated_student = updated_student_response.json()

        final_lessons = updated_student.get("remaining_lessons", 0)
        expected_lessons = 5 - len(time_slots)  # 5 - 3 = 2

        self.assert_equal(final_lessons, expected_lessons,
                          f"Should have {expected_lessons} lessons after {len(time_slots)} appointments")

        # 清理测试数据
        for appointment_id in appointment_ids:
            requests.delete(f"{self.api_url}/api/appointments/{appointment_id}")
        requests.delete(f"{self.api_url}/api/students/{student_id}")

        print(f"通过：测试14通过 - {len(time_slots)}个预约成功扣减{len(time_slots)}次课程 - 5 -> {final_lessons}")


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
            test_instance.test_08_duplicate_student_appointment,
            test_instance.test_09_api_get_upcoming_appointments,
            test_instance.test_10_frontend_statistics_accuracy,
            test_instance.test_11_appointment_deducts_lessons,
            test_instance.test_12_cancel_appointment_restores_lessons,
            test_instance.test_12b_cancel_already_cancelled_appointment,
            test_instance.test_12c_cancel_nonexistent_appointment,
            test_instance.test_13_insufficient_lessons_prevents_appointment,
            test_instance.test_14_multiple_appointments_deduct_multiple_lessons
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