#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本 - 测试学生管理API
"""

import requests
import json
import time
import sys

# 配置
BASE_URL = "http://localhost:8003"
API_BASE = f"{BASE_URL}/api"

def log(msg):
    """打印日志"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def test_connection():
    """测试连接"""
    log("Testing connection...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            log("Connection OK")
            return True
        else:
            log(f"Connection failed: {response.status_code}")
            return False
    except Exception as e:
        log(f"Connection error: {e}")
        return False

def test_create_student():
    """测试创建学生"""
    log("Testing create student...")

    # 生成唯一名字
    unique_name = f"TestStudent_{int(time.time())}"

    test_data = {
        "name": unique_name,
        "nickname": "Tester",
        "learning_item": "蛙泳",
        "package_type": "1v1",
        "total_lessons": 10,
        "price": 2000,
        "venue_share": 500,
        "id_card": "110101200001011234",
        "phone": "13800138000",
        "note": "Test student creation"
    }

    try:
        response = requests.post(f"{API_BASE}/students/", json=test_data, timeout=10)

        if response.status_code == 200:
            student = response.json()
            student_id = student.get("id") or student.get("_id")
            log(f"Create student OK: ID={student_id}")
            log(f"  ID Card: {student.get('id_card')}")
            log(f"  Phone: {student.get('phone')}")
            return student_id
        else:
            log(f"Create student failed: {response.status_code}")
            log(f"  Response: {response.text}")
            return None

    except Exception as e:
        log(f"Create student error: {e}")
        return None

def test_get_student(student_id):
    """测试获取学生"""
    log("Testing get student...")

    if not student_id:
        log("No student ID, skipping")
        return False

    try:
        response = requests.get(f"{API_BASE}/students/{student_id}", timeout=10)

        if response.status_code == 200:
            student = response.json()
            log(f"Get student OK:")
            log(f"  Name: {student.get('name')}")
            log(f"  ID Card: {student.get('id_card')}")
            log(f"  Phone: {student.get('phone')}")
            return True
        else:
            log(f"Get student failed: {response.status_code}")
            return False

    except Exception as e:
        log(f"Get student error: {e}")
        return False

def test_update_student(student_id):
    """测试更新学生"""
    log("Testing update student...")

    if not student_id:
        log("No student ID, skipping")
        return False

    update_data = {
        "name": f"Updated_{int(time.time())}",
        "nickname": "Updated Tester",
        "id_card": "220101199501015678",
        "phone": "13912345678",
        "note": "Updated test student"
    }

    try:
        response = requests.put(f"{API_BASE}/students/{student_id}", json=update_data, timeout=10)

        if response.status_code == 200:
            student = response.json()
            log(f"Update student OK:")
            log(f"  ID Card: {student.get('id_card')}")
            log(f"  Phone: {student.get('phone')}")
            return True
        else:
            log(f"Update student failed: {response.status_code}")
            log(f"  Response: {response.text}")
            return False

    except Exception as e:
        log(f"Update student error: {e}")
        return False

def test_delete_student(student_id):
    """测试删除学生"""
    log("Testing delete student...")

    if not student_id:
        log("No student ID, skipping")
        return False

    try:
        response = requests.delete(f"{API_BASE}/students/{student_id}", timeout=10)

        if response.status_code == 200:
            log("Delete student OK")
            return True
        else:
            log(f"Delete student failed: {response.status_code}")
            return False

    except Exception as e:
        log(f"Delete student error: {e}")
        return False

def main():
    """主函数"""
    log("Starting student management API tests")
    log("=" * 50)

    passed = 0
    failed = 0

    # 测试连接
    if test_connection():
        passed += 1
    else:
        failed += 1
        log("Cannot connect to server, stopping tests")
        return 1

    # 测试创建学生
    student_id = test_create_student()
    if student_id:
        passed += 1
    else:
        failed += 1

    # 测试获取学生
    if test_get_student(student_id):
        passed += 1
    else:
        failed += 1

    # 测试更新学生
    if test_update_student(student_id):
        passed += 1
    else:
        failed += 1

    # 测试删除学生
    if test_delete_student(student_id):
        passed += 1
    else:
        failed += 1

    # 打印结果
    log("=" * 50)
    log("Test Summary:")
    log(f"  Passed: {passed}")
    log(f"  Failed: {failed}")
    log(f"  Total:  {passed + failed}")

    if failed == 0:
        log("All tests PASSED!")
        return 0
    else:
        log("Some tests FAILED!")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        log(f"Test script error: {e}")
        sys.exit(1)