#!/usr/bin/env python3
"""
云端数据库索引检查和清理脚本
这个脚本用于检查和删除云端MongoDB的唯一索引，使其与本地环境保持一致
"""

import asyncio
import sys
import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import OperationFailure

# MongoDB连接配置 - 从部署文档获取
MONGODB_URI = "mongodb://easy-book:JYWSRNKNJ0JFlQGn6H1@10.0.20.14:27017/easy_book?authSource=admin"
DATABASE_NAME = "easy_book"

async def check_and_clean_cloud_indexes():
    """检查和清理云端数据库的唯一索引"""
    print("🔍 开始检查云端MongoDB索引...")

    try:
        # 连接到云端MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]

        print(f"✅ 成功连接到数据库: {DATABASE_NAME}")

        # 获取所有集合
        collections = ["students", "appointments", "attendances"]

        for collection_name in collections:
            print(f"\n📋 检查集合: {collection_name}")
            collection = db[collection_name]

            # 获取现有索引
            existing_indexes = []
            try:
                for index in collection.list_indexes():
                    existing_indexes.append(index)
                    print(f"  现有索引: {index['name']} - {index['key']} (唯一: {index.get('unique', False)})")
            except Exception as e:
                print(f"  ⚠️ 无法获取索引信息: {e}")
                continue

            # 检查并删除唯一索引
            for index in existing_indexes:
                if index.get('unique', False):
                    index_name = index['name']
                    print(f"  🗑️  发现唯一索引: {index_name} - 正在删除...")

                    try:
                        collection.drop_index(index_name)
                        print(f"  ✅ 成功删除唯一索引: {index_name}")
                    except OperationFailure as e:
                        if "not found" in str(e):
                            print(f"  ⚠️  索引不存在: {index_name}")
                        else:
                            print(f"  ❌ 删除索引失败: {index_name} - {e}")
                    except Exception as e:
                        print(f"  ❌ 删除索引时发生错误: {index_name} - {e}")

        print(f"\n🎯 云端数据库索引清理完成！")
        print(f"   所有唯一索引已被删除，现在与本地环境保持一致")

        # 关闭连接
        client.close()
        print(f"✅ 数据库连接已关闭")

    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False

    return True

def main():
    """主函数"""
    print("🚀 云端数据库索引清理工具")
    print("=" * 50)
    print("用途: 删除云端MongoDB的所有唯一索引")
    print("确保: 云端环境与本地环境保持一致")
    print("=" * 50)

    # 运行异步函数
    success = asyncio.run(check_and_clean_cloud_indexes())

    if success:
        print("\n🎉 任务完成！")
        print("现在可以重新部署应用程序，新的索引系统会自动创建查询优化索引。")
    else:
        print("\n❌ 任务失败！")
        print("请检查数据库连接配置和权限。")

if __name__ == "__main__":
    main()