#!/usr/bin/env python3
"""
直接上传文件到服务器脚本
通过SCP直接传输，无需git
"""
import os
import subprocess
import sys

# 服务器配置
SERVER_IP = "49.233.60.29"
SERVER_USER = "ubuntu"
SERVER_PATH = "/home/admin/easy-book"

# 本地项目路径
LOCAL_PATH = os.path.dirname(os.path.abspath(__file__))

# 需要上传的文件和目录
UPLOAD_FILES = [
    # 后端文件 - 上传到 /home/admin/easy-book/backend/backend/
    "backend/api_server/",
    "backend/requirements.txt",
    "backend/run.py",

    # 配置文件
    ".env.example",

    # 脚本文件
    "cloud_index_check.py",
]

# 需要在服务器上创建的目录
CREATE_DIRS = [
    "backend",
    "backend/backend",
    "backend/frontend",
    "doc"
]

def run_command(command, check=True):
    """执行命令并处理错误"""
    print(f"执行: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        if not check:
            return False
    return True

def upload_files():
    """上传文件到服务器"""
    print("开始上传文件到服务器...")

    # 1. 在服务器上创建必要的目录
    print("\n创建服务器目录...")
    for dir_path in CREATE_DIRS:
        run_command(f'ssh {SERVER_USER}@{SERVER_IP} "mkdir -p {SERVER_PATH}/{dir_path}"')

    # 2. 上传文件和目录
    print("\n上传文件和目录...")
    for file_path in UPLOAD_FILES:
        local_full_path = os.path.join(LOCAL_PATH, file_path)
        if os.path.exists(local_full_path):
            if os.path.isdir(local_full_path):
                # 上传目录
                cmd = f'scp -r "{local_full_path}" {SERVER_USER}@{SERVER_IP}:{SERVER_PATH}/'
            else:
                # 上传文件
                cmd = f'scp "{local_full_path}" {SERVER_USER}@{SERVER_IP}:{SERVER_PATH}/'

            success = run_command(cmd)
            if success:
                print(f"  [OK] {file_path}")
            else:
                print(f"  [FAIL] {file_path} (上传失败)")
        else:
            print(f"  [WARN] {file_path} (文件不存在)")

def setup_server():
    """在服务器上执行设置"""
    print("\n服务器设置...")

    # 检查和清理云端唯一索引
    run_command(f'ssh {SERVER_USER}@{SERVER_IP} "cd {SERVER_PATH} && python cloud_index_check.py"', check=False)

    # 安装依赖
    print("\n安装依赖...")
    run_command(f'ssh {SERVER_USER}@{SERVER_IP} "cd {SERVER_PATH} && python3 -m pip install -r backend/requirements.txt"', check=False)

    # 启动服务 - 按照部署文档的方式
    print("\n启动服务...")
    run_command(f'ssh {SERVER_USER}@{SERVER_IP} "pkill -f \'python3 run.py\' || true"', check=False)
    run_command(f'ssh {SERVER_USER}@{SERVER_IP} "cd {SERVER_PATH}/backend/backend && nohup python3 run.py 8002 > /tmp/backend.log 2>&1 &"', check=False)

def check_services():
    """检查服务状态"""
    print("\n检查服务状态...")

    # 检查后端服务
    result = run_command(f'ssh {SERVER_USER}@{SERVER_IP} "ps aux | grep \'python3 run.py\'"', check=False)
    if result and result.strip():
        print("  [OK] 后端服务运行中")
    else:
        print("  [FAIL] 后端服务未运行")

    # 测试后端健康检查
    result = run_command(f'ssh {SERVER_USER}@{SERVER_IP} "curl -s http://localhost:8002/health"', check=False)
    if result and result.strip():
        print("  [OK] 后端健康检查通过")
    else:
        print("  [FAIL] 后端健康检查失败")

def main():
    """主函数"""
    print("=" * 50)
    print("Easy Book 服务器部署工具")
    print("=" * 50)
    print(f"服务器: {SERVER_IP}")
    print(f"路径: {SERVER_PATH}")
    print("=" * 50)

    try:
        upload_files()
        setup_server()
        check_services()

        print("\n" + "=" * 50)
        print("[SUCCESS] 部署完成！")
        print("=" * 50)
        print(f"访问地址:")
        print(f"   后端API: http://{SERVER_IP}:8002")
        print(f"   前端应用: http://{SERVER_IP}")
        print(f"   查看日志: ssh {SERVER_USER}@{SERVER_IP} 'tail -f /tmp/backend.log'")
        print("=" * 50)

    except Exception as e:
        print(f"\n[ERROR] 部署失败: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())