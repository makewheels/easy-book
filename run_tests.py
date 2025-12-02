#!/usr/bin/env python3
"""
快速运行测试脚本
"""

import subprocess
import sys
import os

def check_requirements():
    """检查测试依赖"""
    try:
        import requests
        print("[OK] requests库已安装")
    except ImportError:
        print("[ERROR] requests库未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        print("[OK] requests库安装完成")

def main():
    """主函数"""
    print("泳课预约系统自动化测试")
    print("=" * 40)

    # 检查依赖
    check_requirements()

    # 切换到项目根目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 运行测试
    test_file = "test_student_management.py"
    if os.path.exists(test_file):
        print(f"运行测试文件: {test_file}")
        print("-" * 40)

        try:
            result = subprocess.run([sys.executable, test_file],
                                  capture_output=False,
                                  text=True)
            return result.returncode
        except KeyboardInterrupt:
            print("\n测试被用户中断")
            return 1
        except Exception as e:
            print(f"运行测试时出错: {e}")
            return 1
    else:
        print(f"[ERROR] 测试文件不存在: {test_file}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n测试结束，退出码: {exit_code}")
    sys.exit(exit_code)