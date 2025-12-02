#!/usr/bin/env python3
"""
泳课预约系统自动化测试脚本
测试学生管理模块的身份证号码和手机号功能
"""

import requests
import json
import time
import random
import string
from typing import Dict, Any, Optional

class TestConfig:
    """测试配置类"""
    BASE_URL = "http://localhost:8003"
    API_BASE = f"{BASE_URL}/api"

    # 测试数据
    TEST_STUDENT = {
        "name": "自动化测试学员",
        "nickname": "自动测试",
        "learning_item": "蛙泳",
        "package_type": "1v1",
        "total_lessons": 10,
        "price": 2000,
        "venue_share": 500,
        "id_card": "110101200001011234",
        "phone": "13800138000",
        "note": "自动化测试创建的学员"
    }

    UPDATE_DATA = {
        "name": "自动化测试学员-已更新",
        "nickname": "更新测试",
        "id_card": "220101199501015678",
        "phone": "13912345678",
        "note": "自动化测试更新的学员信息"
    }

class StudentAPITest:
    """学生API测试类"""

    def __init__(self):
        self.config = TestConfig()
        self.session = requests.Session()
        self.created_student_id = None

    def generate_unique_name(self, prefix: str = "测试学员") -> str:
        """生成唯一的学生姓名"""
        timestamp = int(time.time())
        random_suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
        return f"{prefix}_{timestamp}_{random_suffix}"

    def log_test(self, test_name: str, status: str, details: str = ""):
        """记录测试日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {test_name}: {status}")
        if details:
            print(f"    Details: {details}")

    def test_health_check(self) -> bool:
        """测试服务健康检查"""
        try:
            response = self.session.get(f"{self.config.BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("服务健康检查", "PASSED", f"Status code: {response.status_code}")
                return True
            else:
                self.log_test("服务健康检查", "FAILED", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("服务健康检查", "FAILED", f"Connection error: {e}")
            return False

    def test_create_student(self) -> bool:
        """测试创建学生"""
        try:
            # 生成唯一姓名避免冲突
            test_data = self.config.TEST_STUDENT.copy()
            test_data["name"] = self.generate_unique_name("自动化测试学员")

            response = self.session.post(
                f"{self.config.API_BASE}/students/",
                json=test_data,
                timeout=10
            )

            if response.status_code == 200:
                student_data = response.json()
                self.created_student_id = student_data.get("id") or student_data.get("_id")

                # 验证返回的数据包含身份证和手机号
                if (student_data.get("id_card") == test_data["id_card"] and
                    student_data.get("phone") == test_data["phone"]):
                    self.log_test("创建学生", "✅ 通过",
                                f"ID: {self.created_student_id}, 身份证: {student_data.get('id_card')}, 手机: {student_data.get('phone')}")
                    return True
                else:
                    self.log_test("创建学生", "❌ 失败", "身份证或手机号数据不匹配")
                    return False
            else:
                self.log_test("创建学生", "❌ 失败", f"状态码: {response.status_code}, 响应: {response.text}")
                return False

        except Exception as e:
            self.log_test("创建学生", "❌ 失败", f"异常: {e}")
            return False

    def test_get_students(self) -> bool:
        """测试获取学生列表"""
        try:
            response = self.session.get(f"{self.config.API_BASE}/students/", timeout=10)

            if response.status_code == 200:
                students = response.json()
                # 查找我们刚创建的学生
                found_student = None
                for student in students:
                    if (student.get("id") == self.created_student_id or
                        student.get("_id") == self.created_student_id):
                        found_student = student
                        break

                if found_student:
                    self.log_test("获取学生列表", "✅ 通过",
                                f"找到创建的学生，身份证: {found_student.get('id_card')}, 手机: {found_student.get('phone')}")
                    return True
                else:
                    self.log_test("获取学生列表", "❌ 失败", "在列表中未找到创建的学生")
                    return False
            else:
                self.log_test("获取学生列表", "❌ 失败", f"状态码: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("获取学生列表", "❌ 失败", f"异常: {e}")
            return False

    def test_get_student_by_id(self) -> bool:
        """测试根据ID获取学生"""
        if not self.created_student_id:
            self.log_test("根据ID获取学生", "⏭️ 跳过", "没有学生ID")
            return True

        try:
            response = self.session.get(
                f"{self.config.API_BASE}/students/{self.created_student_id}",
                timeout=10
            )

            if response.status_code == 200:
                student = response.json()
                if (student.get("id_card") and student.get("phone")):
                    self.log_test("根据ID获取学生", "✅ 通过",
                                f"身份证: {student.get('id_card')}, 手机: {student.get('phone')}")
                    return True
                else:
                    self.log_test("根据ID获取学生", "❌ 失败", "身份证或手机号字段为空")
                    return False
            else:
                self.log_test("根据ID获取学生", "❌ 失败", f"状态码: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("根据ID获取学生", "❌ 失败", f"异常: {e}")
            return False

    def test_update_student(self) -> bool:
        """测试更新学生信息"""
        if not self.created_student_id:
            self.log_test("更新学生信息", "⏭️ 跳过", "没有学生ID")
            return True

        try:
            response = self.session.put(
                f"{self.config.API_BASE}/students/{self.created_student_id}",
                json=self.config.UPDATE_DATA,
                timeout=10
            )

            if response.status_code == 200:
                updated_student = response.json()

                # 验证身份证和手机号是否正确更新
                if (updated_student.get("id_card") == self.config.UPDATE_DATA["id_card"] and
                    updated_student.get("phone") == self.config.UPDATE_DATA["phone"]):
                    self.log_test("更新学生信息", "✅ 通过",
                                f"更新后身份证: {updated_student.get('id_card')}, 手机: {updated_student.get('phone')}")
                    return True
                else:
                    self.log_test("更新学生信息", "❌ 失败", "身份证或手机号更新失败")
                    return False
            else:
                self.log_test("更新学生信息", "❌ 失败", f"状态码: {response.status_code}, 响应: {response.text}")
                return False

        except Exception as e:
            self.log_test("更新学生信息", "❌ 失败", f"异常: {e}")
            return False

    def test_updated_student_data(self) -> bool:
        """测试验证更新后的数据"""
        if not self.created_student_id:
            self.log_test("验证更新后数据", "⏭️ 跳过", "没有学生ID")
            return True

        try:
            response = self.session.get(
                f"{self.config.API_BASE}/students/{self.created_student_id}",
                timeout=10
            )

            if response.status_code == 200:
                student = response.json()

                # 验证所有字段是否正确更新
                checks = [
                    ("姓名", student.get("name"), self.config.UPDATE_DATA["name"]),
                    ("别称", student.get("nickname"), self.config.UPDATE_DATA["nickname"]),
                    ("身份证", student.get("id_card"), self.config.UPDATE_DATA["id_card"]),
                    ("手机号", student.get("phone"), self.config.UPDATE_DATA["phone"]),
                    ("备注", student.get("note"), self.config.UPDATE_DATA["note"])
                ]

                all_passed = True
                for field_name, actual, expected in checks:
                    if actual != expected:
                        self.log_test("验证更新后数据", "❌ 失败",
                                    f"{field_name}不匹配: 期望={expected}, 实际={actual}")
                        all_passed = False

                if all_passed:
                    self.log_test("验证更新后数据", "✅ 通过", "所有字段都正确更新")
                    return True
                return False
            else:
                self.log_test("验证更新后数据", "❌ 失败", f"状态码: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("验证更新后数据", "❌ 失败", f"异常: {e}")
            return False

    def test_delete_student(self) -> bool:
        """测试删除学生"""
        if not self.created_student_id:
            self.log_test("删除学生", "⏭️ 跳过", "没有学生ID")
            return True

        try:
            response = self.session.delete(
                f"{self.config.API_BASE}/students/{self.created_student_id}",
                timeout=10
            )

            if response.status_code == 200:
                self.log_test("删除学生", "✅ 通过", f"删除的学生ID: {self.created_student_id}")
                self.created_student_id = None
                return True
            else:
                self.log_test("删除学生", "❌ 失败", f"状态码: {response.status_code}")
                return False

        except Exception as e:
            self.log_test("删除学生", "❌ 失败", f"异常: {e}")
            return False

    def cleanup(self):
        """清理测试数据"""
        if self.created_student_id:
            try:
                self.session.delete(
                    f"{self.config.API_BASE}/students/{self.created_student_id}",
                    timeout=5
                )
                self.log_test("清理测试数据", "✅ 完成", f"删除学生ID: {self.created_student_id}")
            except:
                self.log_test("清理测试数据", "⚠️ 失败", "无法删除测试数据")

    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("=" * 60)
        print("泳课预约系统自动化测试开始")
        print("测试重点: 学生管理模块的身份证号码和手机号功能")
        print("=" * 60)

        test_results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "test_details": []
        }

        tests = [
            ("服务健康检查", self.test_health_check),
            ("创建学生", self.test_create_student),
            ("获取学生列表", self.test_get_students),
            ("根据ID获取学生", self.test_get_student_by_id),
            ("更新学生信息", self.test_update_student),
            ("验证更新后数据", self.test_updated_student_data),
            ("删除学生", self.test_delete_student),
        ]

        try:
            for test_name, test_func in tests:
                test_results["total_tests"] += 1

                try:
                    result = test_func()
                    if result is True:
                        test_results["passed_tests"] += 1
                        test_results["test_details"].append({"name": test_name, "status": "PASSED"})
                    elif result is False:
                        test_results["failed_tests"] += 1
                        test_results["test_details"].append({"name": test_name, "status": "FAILED"})
                    else:  # None or skipped
                        test_results["skipped_tests"] += 1
                        test_results["test_details"].append({"name": test_name, "status": "SKIPPED"})

                    # 测试间隔
                    time.sleep(0.5)

                except Exception as e:
                    test_results["failed_tests"] += 1
                    test_results["test_details"].append({"name": test_name, "status": "ERROR", "error": str(e)})
                    self.log_test(test_name, "❌ 异常", str(e))

        finally:
            # 清理测试数据
            self.cleanup()

        return test_results

def print_test_summary(results: Dict[str, Any]):
    """打印测试摘要"""
    print("\n" + "=" * 60)
    print("测试摘要")
    print("=" * 60)
    print(f"总测试数: {results['total_tests']}")
    print(f"通过: {results['passed_tests']} ✅")
    print(f"失败: {results['failed_tests']} ❌")
    print(f"跳过: {results['skipped_tests']} ⏭️")

    success_rate = 0
    if results['total_tests'] > 0:
        success_rate = (results['passed_tests'] / results['total_tests']) * 100

    print(f"成功率: {success_rate:.1f}%")

    print("\n详细结果:")
    for detail in results['test_details']:
        status_icon = {
            "PASSED": "✅",
            "FAILED": "❌",
            "SKIPPED": "⏭️",
            "ERROR": "💥"
        }
        icon = status_icon.get(detail['status'], "❓")
        error_info = f" - {detail.get('error', '')}" if detail.get('error') else ""
        print(f"  {icon} {detail['name']}{error_info}")

    print("\n" + "=" * 60)

    if success_rate >= 80:
        print("🎉 测试整体通过！身份证号码和手机号功能工作正常。")
    elif success_rate >= 60:
        print("⚠️ 测试部分通过，但存在一些问题需要修复。")
    else:
        print("❌ 测试失败较多，需要重点检查相关功能。")

def main():
    """主函数"""
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(2)

    # 运行测试
    tester = StudentAPITest()
    results = tester.run_all_tests()

    # 打印摘要
    print_test_summary(results)

    # 返回退出码
    exit_code = 0 if results['failed_tests'] == 0 else 1
    return exit_code

if __name__ == "__main__":
    exit(main())