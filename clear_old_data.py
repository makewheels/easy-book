#!/usr/bin/env python3
"""
清理数据库中的旧预约数据
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
from api_server.mongo_database import MongoDatabase

async def clear_old_appointments():
    """清空旧预约数据"""
    print("开始清理旧预约数据...")

    db = MongoDatabase()
    await db.connect()

    try:
        # 删除所有预约数据
        result = await db.db.appointments.delete_many({})
        print(f"已删除 {result.deleted_count} 条预约记录")

        # 删除所有考勤数据
        result = await db.db.attendances.delete_many({})
        print(f"已删除 {result.deleted_count} 条考勤记录")

        print("✅ 数据清理完成！")

    except Exception as e:
        print(f"❌ 清理失败: {e}")
        return False

    finally:
        await db.client.close()

    return True

if __name__ == "__main__":
    asyncio.run(clear_old_appointments())