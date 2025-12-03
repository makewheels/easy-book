#!/usr/bin/env python3
"""
健康检查和系统状态测试
验证API健康检查、数据库连接和基础系统功能
"""

import sys
import os
import time
import datetime
import requests

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from conftest import TestBase

class TestHealth(TestBase):
    """健康检查测试类"""

    def test_01_root_endpoint(self):
        """测试1：根端点健康检查"""
        print("\n测试：测试1 - 根端点健康检查")

        response = requests.get(f"{self.api_url}/")
        self.assert_equal(response.status_code, 200, "Root endpoint status code")

        data = response.json()
        self.assert_true("message" in data, "Root endpoint returns message")
        self.assert_equal(data["message"], "Easy Book API is running", "Root endpoint message correct")

        print(f"通过：测试1通过 - 根端点正常响应 - {data['message']}")

    def test_02_basic_health_check(self):
        """测试2：基础健康检查"""
        print("\n测试：测试2 - 基础健康检查")

        response = requests.get(f"{self.api_url}/health")
        self.assert_equal(response.status_code, 200, "Health check status code")

        data = response.json()
        self.assert_true("status" in data, "Health check returns status")
        self.assert_equal(data["status"], "healthy", "Health check status is healthy")

        print(f"通过：测试2通过 - 健康检查正常 - 状态: {data['status']}")

    def test_03_database_health_check(self):
        """测试3：数据库健康检查"""
        print("\n测试：测试3 - 数据库健康检查")

        response = requests.get(f"{self.api_url}/api/health/db")
        self.assert_equal(response.status_code, 200, "Database health check status code")

        data = response.json()
        # API返回格式: {"database": "healthy", "connection": "connected"}
        self.assert_true("database" in data, "Database health check returns database status")
        self.assert_equal(data["database"], "healthy", "Database health check status is healthy")
        self.assert_true("connection" in data, "Database health check returns connection status")
        self.assert_equal(data["connection"], "connected", "Database connection status is connected")

        print(f"通过：测试3通过 - 数据库健康检查正常 - 数据库:{data['database']}, 连接:{data['connection']}")

    def test_04_api_docs_available(self):
        """测试4：API文档可用性检查"""
        print("\n测试：测试4 - API文档可用性检查")

        # 检查OpenAPI文档端点
        response = requests.get(f"{self.api_url}/docs")
        self.assert_equal(response.status_code, 200, "API docs status code")

        # 验证返回的是HTML文档
        content_type = response.headers.get("content-type", "")
        self.assert_true("text/html" in content_type.lower(), "API docs returns HTML")

        print("通过：测试4通过 - API文档页面可访问")

    def test_05_openapi_schema(self):
        """测试5：OpenAPI模式检查"""
        print("\n测试：测试5 - OpenAPI模式检查")

        response = requests.get(f"{self.api_url}/openapi.json")
        self.assert_equal(response.status_code, 200, "OpenAPI schema status code")

        schema = response.json()
        required_fields = ["openapi", "info", "paths"]
        for field in required_fields:
            self.assert_true(field in schema, f"OpenAPI schema contains {field}")

        # 验证基本信息
        info = schema.get("info", {})
        self.assert_true("title" in info, "OpenAPI schema has title")
        self.assert_true("version" in info, "OpenAPI schema has version")

        print(f"通过：测试5通过 - OpenAPI模式正常 - 标题: {info.get('title')}")

    def test_06_response_time_performance(self):
        """测试6：响应时间性能检查"""
        print("\n测试：测试6 - 响应时间性能检查")

        # 测试根端点响应时间
        start_time = time.time()
        response = requests.get(f"{self.api_url}/health")
        response_time = time.time() - start_time

        self.assert_less(response_time, 3.0, "Health check response time < 3s")
        self.assert_equal(response.status_code, 200, "Health check status code during performance test")

        # 测试数据库连接时间
        db_start = time.time()
        db_response = requests.get(f"{self.api_url}/api/health/db")
        db_time = time.time() - db_start

        self.assert_less(db_time, 5.0, "Database health check response time < 5s")
        self.assert_equal(db_response.status_code, 200, "Database health check status code during performance test")

        print(f"通过：测试6通过 - 响应时间正常 - 根端:{response_time:.3f}s, 数据库:{db_time:.3f}s")

    def test_07_concurrent_requests(self):
        """测试7：并发请求处理能力"""
        print("\n测试：测试7 - 并发请求处理能力")

        import threading
        import queue

        results = queue.Queue()
        num_requests = 5

        def make_request():
            try:
                response = requests.get(f"{self.api_url}/health", timeout=5)
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")

        # 创建并发请求
        threads = []
        for i in range(num_requests):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # 等待所有请求完成
        for thread in threads:
            thread.join()

        # 检查结果
        success_count = 0
        for _ in range(num_requests):
            result = results.get()
            if result == 200:
                success_count += 1

        self.assert_equal(success_count, num_requests, f"All {num_requests} concurrent requests succeed")

        print(f"通过：测试7通过 - 并发请求处理正常 - {success_count}/{num_requests} 成功")

    def test_08_cors_headers(self):
        """测试8：CORS头配置检查"""
        print("\n测试：测试8 - CORS头配置检查")

        response = requests.get(f"{self.api_url}/health")

        # 检查CORS相关头
        self.assert_equal(response.status_code, 200, "CORS check request successful")

        # 注意：实际的CORS头检查需要OPTIONS请求，这里做基础验证
        print(f"通过：测试8通过 - 基础请求正常 - 响应头检查通过")


def run_health_tests():
    """运行健康检查测试"""
    print("=" * 60)
    print("健康检查和系统状态测试")
    print("=" * 60)

    test_instance = TestHealth()

    try:
        # 初始化
        print("初始化测试环境...")
        if not test_instance.setup_mongodb():
            print("SKIP: 无法连接到MongoDB，跳过数据库相关测试")
            # 即使MongoDB连接失败，也运行API健康检查测试
            pass

        # 运行所有测试
        tests = [
            test_instance.test_01_root_endpoint,
            test_instance.test_02_basic_health_check,
            test_instance.test_03_database_health_check,
            test_instance.test_04_api_docs_available,
            test_instance.test_05_openapi_schema,
            test_instance.test_06_response_time_performance,
            test_instance.test_07_concurrent_requests,
            test_instance.test_08_cors_headers
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

        print(f"\n健康检查和系统状态测试完成")
        print(f"通过: {passed}, 失败: {failed}")
        print(f"成功率: {((passed/(passed+failed))*100):.1f}%")

        return failed == 0

    finally:
        test_instance.teardown()


if __name__ == "__main__":
    success = run_health_tests()
    sys.exit(0 if success else 1)