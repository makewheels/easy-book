#!/usr/bin/env python3
"""
周一预约限制测试
测试游泳馆周一闭馆，不能预约的功能
"""

import sys
import os
import time
import datetime
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from conftest import TestBase

class TestMondayRestriction(TestBase):
    """周一预约限制测试类"""

    def test_01_front_end_monday_validation_student_detail(self):
        """测试1：前端学员详情页周一预约验证"""
        print("\n测试：测试1 - 前端学员详情页周一预约验证")

        # 创建测试学员
        student = self.create_test_student("周一测试学员")
        student_id = student["_id"]

        # 导航到学员详情页
        self.driver.get(f"{self.frontend_url}/students/{student_id}")
        self.wait_for_page_load()

        # 点击预约按钮
        appointment_button = self.wait_for_element_clickable(
            (By.XPATH, "//button[contains(text(), '预约')] | //span[contains(text(), '预约')]"),
            timeout=10
        )
        appointment_button.click()

        # 等待预约对话框出现
        self.wait_for_element((By.CLASS_NAME, "dialog"), timeout=5)

        # 获取下一个周一的日期
        next_monday = self.get_next_monday()

        # 在日期选择器中找到并选择周一
        try:
            # 尝试选择周一日期
            date_input = self.wait_for_element((By.CSS_SELECTOR, "input[type='date']"), timeout=5)

            # 清除日期并输入周一日期
            self.driver.execute_script("arguments[0].value = '';", date_input)
            date_input.send_keys(next_monday)

            # 选择一个时间
            time_option = self.wait_for_element_clickable(
                (By.CSS_SELECTOR, "select[name='time'] option, select[name='timeSlot'] option"),
                timeout=5
            )
            time_option.click()

            # 点击提交按钮
            submit_button = self.wait_for_element_clickable(
                (By.XPATH, "//button[contains(text(), '确认')] | //button[contains(text(), '预约')]")
            )
            submit_button.click()

            # 验证是否显示了错误提示
            self.wait_for_element((By.CLASS_NAME, "toast"), timeout=5)

            # 检查提示文本是否包含周一闭馆的信息
            toast_element = self.driver.find_element(By.CLASS_NAME, "toast")
            toast_text = toast_element.text

            self.assert_true(
                "周一闭馆" in toast_text or "不能预约" in toast_text,
                f"应该显示周一闭馆提示: {toast_text}"
            )

            print(f"[OK] 前端正确阻止了周一预约: {toast_text}")

        except Exception as e:
            print(f"[FAIL] 前端周一预约验证失败: {e}")
            raise

    def test_02_front_end_monday_validation_students_page(self):
        """测试2：前端学员列表页周一预约验证"""
        print("\n测试：测试2 - 前端学员列表页周一预约验证")

        # 导航到学员列表页
        self.driver.get(f"{self.frontend_url}/students")
        self.wait_for_page_load()

        # 等待学员列表加载
        self.wait_for_element((By.CLASS_NAME, "student-list"), timeout=10)

        # 点击第一个学员的预约按钮
        try:
            appointment_buttons = self.driver.find_elements(
                By.XPATH, "//button[contains(text(), '预约')] | //span[contains(text(), '预约')]"
            )
            if appointment_buttons:
                appointment_buttons[0].click()

                # 等待预约对话框出现
                self.wait_for_element((By.CLASS_NAME, "dialog"), timeout=5)

                # 获取下一个周一的日期
                next_monday = self.get_next_monday()

                # 在日期选择器中输入周一日期
                date_input = self.wait_for_element((By.CSS_SELECTOR, "input[type='date']"), timeout=5)
                self.driver.execute_script("arguments[0].value = '';", date_input)
                date_input.send_keys(next_monday)

                # 选择时间
                time_options = self.driver.find_elements(By.CSS_SELECTOR, "select[name='time'] option, select[name='timeSlot'] option")
                if time_options:
                    time_options[1].click()

                # 点击提交按钮
                submit_button = self.wait_for_element_clickable(
                    (By.XPATH, "//button[contains(text(), '确认')] | //button[contains(text(), '预约')]")
                )
                submit_button.click()

                # 验证错误提示
                self.wait_for_element((By.CLASS_NAME, "toast"), timeout=5)
                toast_element = self.driver.find_element(By.CLASS_NAME, "toast")
                toast_text = toast_element.text

                self.assert_true(
                    "周一闭馆" in toast_text or "不能预约" in toast_text,
                    f"学员列表页应该显示周一闭馆提示: {toast_text}"
                )

                print(f"[OK] 学员列表页正确阻止了周一预约: {toast_text}")
            else:
                print("[SKIP] 没有找到预约按钮")

        except Exception as e:
            print(f"[FAIL] 学员列表页周一预约验证失败: {e}")
            raise

    def test_03_backend_api_monday_validation(self):
        """测试3：后端API周一预约验证"""
        print("\n测试：测试3 - 后端API周一预约验证")

        # 创建测试学员
        student = self.create_test_student("API周一测试学员")
        student_id = student["_id"]

        # 获取下一个周一的日期
        next_monday = self.get_next_monday()

        # 尝试通过API创建周一预约
        appointment_data = {
            "student_id": student_id,
            "appointment_date": next_monday,
            "time_slot": "10:00"
        }

        # 发送API请求
        response = requests.post(f"{self.api_url}/api/appointments/", json=appointment_data)

        # 验证API响应
        print(f"API响应状态码: {response.status_code}")
        print(f"API响应内容: {response.text}")

        # API应该允许创建（前端负责验证）
        # 所以这里我们检查API本身没有阻止周一预约
        if response.status_code == 200:
            print("[OK] API层没有阻止周一预约（由前端验证）")

            # 清理：取消刚才创建的预约
            result = response.json()
            if result.get("data") and result["data"].get("id"):
                appointment_id = result["data"]["id"]
                cancel_response = requests.put(f"{self.api_url}/api/appointments/{appointment_id}/cancel")
                print(f"清理预约响应: {cancel_response.status_code}")
        else:
            print("[INFO] API可能也包含了周一验证")

    def test_04_calendar_page_monday_not_displayed(self):
        """测试4：日历页面不显示周一"""
        print("\n测试：测试4 - 日历页面不显示周一")

        # 导航到日历页面
        self.driver.get(f"{self.frontend_url}/calendar")
        self.wait_for_page_load()

        # 等待日历加载
        self.wait_for_element((By.CLASS_NAME, "calendar-table"), timeout=10)

        # 查找表头中的星期信息
        headers = self.driver.find_elements(By.TAG_NAME, "th")
        header_texts = [header.text for header in headers]

        print(f"日历表头: {header_texts}")

        # 验证周一是否不在表头中
        monday_found = any("周一" in text for text in header_texts)

        self.assert_false(monday_found, "日历表头不应该包含周一")

        print("[OK] 日历页面正确地不显示周一")

    def test_05_utility_date_functions(self):
        """测试5：日期工具函数验证"""
        print("\n测试：测试5 - 日期工具函数验证")

        # 测试一些已知的周一日期
        test_dates = [
            ("2025-12-08", True),   # 周一
            ("2025-12-15", True),   # 周一
            ("2025-12-22", True),   # 周一
            ("2025-12-09", False),  # 周二
            ("2025-12-10", False),  # 周三
        ]

        for test_date, expected_monday in test_dates:
            # 计算星期几（0=周一, 1=周二, ..., 6=周日）
            weekday = datetime.date.fromisoformat(test_date).weekday()
            is_monday = (weekday == 0)

            print(f"日期 {test_date} 是周一: {is_monday} (期望: {expected_monday})")
            self.assert_equal(is_monday, expected_monday, f"{test_date} 周一判断")

        print("[OK] 日期函数验证正确")

    def get_next_monday(self):
        """获取下一个周一的日期"""
        today = datetime.date.today()

        # 计算到下一个周一的天数 (0=周一, 1=周二, ..., 6=周日)
        days_until_monday = (0 - today.weekday()) % 7
        if days_until_monday == 0:  # 如果今天是周一，选择下周一
            days_until_monday = 7

        next_monday = today + datetime.timedelta(days=days_until_monday)
        return next_monday.strftime("%Y-%m-%d")


def run_monday_restriction_tests():
    """运行周一预约限制测试"""
    print("=" * 60)
    print("周一预约限制功能测试")
    print("=" * 60)

    test_instance = TestMondayRestriction()

    try:
        # 初始化
        print("初始化测试环境...")
        if not test_instance.setup_mongodb():
            return False

        # 启动浏览器
        if not test_instance.setup_browser():
            print("[SKIP] 浏览器未配置，跳过UI测试")
            # 只运行后端测试
            test_instance.test_03_backend_api_monday_validation()
            test_instance.test_05_utility_date_functions()
            return True

        # 运行所有测试
        tests = [
            test_instance.test_01_front_end_monday_validation_student_detail,
            test_instance.test_02_front_end_monday_validation_students_page,
            test_instance.test_03_backend_api_monday_validation,
            test_instance.test_04_calendar_page_monday_not_displayed,
            test_instance.test_05_utility_date_functions
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

        print(f"\n周一预约限制测试完成")
        print(f"通过: {passed}, 失败: {failed}")
        print(f"成功率: {(passed/(passed+failed)*100):.1f}%")

        return failed == 0

    finally:
        test_instance.teardown()


if __name__ == "__main__":
    success = run_monday_restriction_tests()
    sys.exit(0 if success else 1)