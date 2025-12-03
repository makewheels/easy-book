#!/usr/bin/env python3
"""
主测试运行器
运行所有模块化测试文件并生成综合测试报告
"""

import sys
import os
import time
import subprocess
from pathlib import Path

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_single_test_module(test_module_name):
    """运行单个测试模块"""
    print(f"\n{'='*60}")
    print(f"运行测试模块: {test_module_name}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        # 运行测试模块
        result = subprocess.run([
            sys.executable,
            f"{test_module_name}.py"
        ], capture_output=True, text=True, encoding='utf-8')

        execution_time = time.time() - start_time

        if result.returncode == 0:
            print(f"PASS {test_module_name} - 通过 ({execution_time:.2f}s)")
            return True, 0, 0, execution_time, result.stdout
        else:
            print(f"FAIL {test_module_name} - 失败 ({execution_time:.2f}s)")
            print(f"错误输出:\n{result.stderr}")
            return False, 0, 1, execution_time, result.stdout

    except Exception as e:
        execution_time = time.time() - start_time
        print(f"ERROR {test_module_name} - 运行异常 ({execution_time:.2f}s): {e}")
        return False, 0, 1, execution_time, str(e)

def parse_test_results(output):
    """解析测试输出，提取通过和失败数量"""
    passed = 0
    failed = 0

    if output is None:
        return passed, failed

    lines = output.split('\n')
    for line in lines:
        if '通过:' in line and '失败:' in line:
            try:
                parts = line.split('失败:')
                if len(parts) >= 2:
                    passed_part = parts[0].replace('通过:', '').strip()
                    failed_part = parts[1].split(',')[0].strip()
                    passed += int(passed_part)
                    failed += int(failed_part)
            except:
                pass
        elif '成功率:' in line:
            # 成功率行，跳过
            continue

    return passed, failed

def main():
    """主函数"""
    print("开始运行完整的模块化测试套件")
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")
    print(f"测试目录: {Path(__file__).parent}")

    # 定义所有测试模块
    test_modules = [
        'test_students',        # 学生管理模块测试
        'test_appointments',    # 预约管理模块测试
        'test_attendance',      # 考勤管理模块测试
        'test_ui_integration',  # UI和集成测试
    ]

    # 运行所有测试模块
    total_passed = 0
    total_failed = 0
    total_time = 0
    module_results = {}

    overall_start_time = time.time()

    for module in test_modules:
        module_file = Path(__file__).parent / f"{module}.py"

        if not module_file.exists():
            print(f"SKIP 跳过不存在的测试模块: {module}")
            continue

        success, passed, failed, exec_time, output = run_single_test_module(module)

        # 解析详细结果
        if passed == 0 and failed == 0:
            passed, failed = parse_test_results(output)

        module_results[module] = {
            'success': success,
            'passed': passed,
            'failed': failed,
            'time': exec_time,
            'output': output
        }

        total_passed += passed
        total_failed += failed
        total_time += exec_time

    overall_time = time.time() - overall_start_time

    # 生成综合报告
    print(f"\n{'='*80}")
    print("测试套件执行完成 - 综合报告")
    print(f"{'='*80}")

    print(f"\n总体统计:")
    print(f"   总测试数: {total_passed + total_failed}")
    print(f"   通过数量: {total_passed}")
    print(f"   失败数量: {total_failed}")
    if (total_passed + total_failed) > 0:
        print(f"   成功率: {((total_passed/(total_passed+total_failed))*100):.1f}%")
    else:
        print(f"   成功率: N/A")
    print(f"   总耗时: {total_time:.2f}s")

    print(f"\n各模块详情:")
    for module, result in module_results.items():
        status = "通过" if result['success'] else "失败"
        total_tests = result['passed'] + result['failed']
        success_rate = ((result['passed']/total_tests)*100) if total_tests > 0 else 0

        print(f"   {module}: {status} | {result['passed']}/{total_tests} ({success_rate:.1f}%) | {result['time']:.2f}s")

    # 显示失败模块的详细信息
    failed_modules = [m for m, r in module_results.items() if not r['success']]
    if failed_modules:
        print(f"\n失败模块详情:")
        for module in failed_modules:
            print(f"\n--- {module} 失败原因 ---")
            output = module_results[module]['output']
            if output is not None:
                if len(output) > 500:
                    print(output[:500] + "...")
                else:
                    print(output)
            else:
                print("无详细错误信息")

    # 系统环境信息
    print(f"\n系统环境:")
    print(f"   Python: {sys.version}")
    print(f"   平台: {sys.platform}")
    print(f"   工作目录: {os.getcwd()}")

    # 测试建议
    if total_failed > 0:
        print(f"\n建议:")
        print(f"   1. 检查失败模块的具体错误信息")
        print(f"   2. 确保后端服务运行在正确端口 (http://localhost:8004)")
        print(f"   3. 确保前端服务运行在正确端口 (http://localhost:5174)")
        print(f"   4. 确保MongoDB服务正常运行")
        print(f"   5. 检查网络连接和服务依赖")

    print(f"\n{'='*80}")

    # 返回是否所有测试都通过
    return total_failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)