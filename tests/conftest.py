#!/usr/bin/env python3
"""
自动化测试配置文件
提供测试基础类和工具函数
"""

import os
import time
import datetime
import requests
import re
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class TestBase:
    """测试基础类，提供通用功能"""

    def __init__(self):
        self.api_url = "http://localhost:8004"
        self.frontend_url = "http://localhost:5174"
        self.db = None
        self.driver = None
        self.test_data = {}

    def setup_mongodb(self):
        """初始化MongoDB连接"""
        try:
            mongodb_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
            client = MongoClient(mongodb_url)
            self.db = client.easy_book
            print("PASS: MongoDB connection successful")
            return True
        except Exception as e:
            print(f"FAIL: MongoDB connection failed: {e}")
            return False

    def setup_browser(self):
        """初始化浏览器"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=430,932')  # 移动端尺寸

            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            print("PASS: Chrome browser initialized successfully")
            return True
        except Exception as e:
            print(f"FAIL: Browser initialization failed: {e}")
            return False

    def cleanup_test_data(self):
        """清理测试数据"""
        if self.db is not None:
            try:
                # 删除测试创建的学生
                if "student" in self.test_data:
                    student_id = self.test_data["student"].get("_id") or self.test_data["student"].get("id")
                    if student_id:
                        self.db.students.delete_one({"_id": student_id})

                # 删除测试创建的预约
                if "appointment" in self.test_data:
                    appointment_id = self.test_data["appointment"].get("_id") or self.test_data["appointment"].get("id")
                    if appointment_id:
                        self.db.appointments.delete_one({"_id": appointment_id})

                # 删除考勤记录
                if "student_id" in self.test_data:
                    self.db.attendances.delete_many({"student_id": self.test_data["student_id"]})

                print("PASS: Test data cleaned up successfully")
            except Exception as e:
                print(f"WARN: Test data cleanup failed: {e}")

    def teardown(self):
        """清理资源"""
        self.cleanup_test_data()

        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def assert_equal(self, actual, expected, message=""):
        """断言相等"""
        if actual != expected:
            raise AssertionError(f"{message} - Expected: {expected}, Actual: {actual}")

    def assert_true(self, condition, message=""):
        """断言为真"""
        if not condition:
            raise AssertionError(f"{message} - Expected: True, Actual: False")

    def assert_contains(self, text, substring, message=""):
        """断言包含子字符串"""
        if substring not in text:
            raise AssertionError(f"{message} - '{substring}' not found in '{text}'")

    def assert_less(self, actual, expected, message=""):
        """断言小于"""
        if not (actual < expected):
            raise AssertionError(f"{message} - Expected: < {expected}, Actual: {actual}")

    def wait_for_element(self, by, value, timeout=10):
        """等待元素出现"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def wait_for_element_clickable(self, locator, timeout=10):
        """等待元素可点击"""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )

    def wait_for_page_load(self, timeout=30):
        """等待页面加载完成"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            # 额外等待Vue应用加载
            time.sleep(2)
        except Exception as e:
            print(f"WARN: Page load timeout: {e}")
            # 继续执行，可能页面已经部分加载

    def safe_get_page_source(self):
        """安全获取页面源码，处理编码问题"""
        try:
            page_source = self.driver.page_source
            # 移除所有可能导致编码问题的特殊字符
            page_source = re.sub(r'[^\x00-\xFFFF]+', '', page_source)
            # 确保UTF-8编码兼容
            page_source = page_source.encode('utf-8', errors='ignore').decode('utf-8')
            return page_source
        except Exception as e:
            print(f"WARN: Failed to get page source: {e}")
            return ""

    def create_test_student(self, name_prefix="Test Student"):
        """创建测试学生"""
        student_data = {
            "name": f"{name_prefix} - {datetime.datetime.now().strftime('%H%M%S')}",
            "learning_item": "自由泳",
            "package_type": "1v1",
            "total_lessons": 10,
            "price": 1000,
            "venue_share": 300
        }

        response = requests.post(f"{self.api_url}/api/students/", json=student_data)
        self.assert_equal(response.status_code, 200, "Create student status code")

        student = response.json()  # API returns data directly, not wrapped
        self.test_data["student"] = student
        self.test_data["student_id"] = student.get("_id")  # Use _id instead of id

        return student

    def create_test_appointment(self, student_id=None, date=None, time_slot=None):
        """创建测试预约"""
        if not student_id:
            student_id = self.test_data.get("student_id")
        if not date:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        if not time_slot:
            # 使用辅助函数获取无冲突时间
            time_slot = self.get_test_time_slot(1)  # 23:00

        # 构造开始和结束时间
        hour, minute = map(int, time_slot.split(':'))
        start_datetime = datetime.datetime.strptime(f"{date} {time_slot}", "%Y-%m-%d %H:%M")
        end_datetime = start_datetime + datetime.timedelta(hours=1)  # 默认1小时课程

        appointment_data = {
            "student_id": student_id,
            "start_time": start_datetime.isoformat(),
            "end_time": end_datetime.isoformat(),
            # 兼容性字段
            "appointment_date": date,
            "time_slot": time_slot
        }

        response = requests.post(f"{self.api_url}/api/appointments/", json=appointment_data)
        self.assert_equal(response.status_code, 200, "Create appointment status code")

        # Appointment API returns data wrapped in {"data": {...}}
        appointment = response.json().get("data", {})
        self.test_data["appointment"] = appointment
        self.test_data["appointment_id"] = appointment.get("id")  # Appointment uses id, not _id

        return appointment

    def get_today_date(self):
        """获取今天的日期"""
        return datetime.datetime.now().strftime("%Y-%m-%d")

    def get_test_time_slot(self, hour_offset=0):
        """获取测试用的时间槽，避免与现有预约冲突"""
        # 使用较晚的时间（22:00之后）避免冲突
        base_hour = 22 + hour_offset
        if base_hour >= 24:
            base_hour = base_hour - 24
        return f"{base_hour:02d}:00"

    def get_tomorrow_date(self):
        """获取明天的日期"""
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d")

    def cleanup_appointments(self):
        """清理所有预约数据"""
        try:
            if self.db:
                # 删除所有预约
                self.db.appointments.delete_many({})
                print("INFO: All appointments cleaned up")
        except Exception as e:
            print(f"WARN: Failed to clean up appointments: {e}")