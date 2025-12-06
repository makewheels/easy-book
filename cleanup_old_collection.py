import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def cleanup_old_collection():
    """清理旧的 student_appointments 集合"""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.easy_book

    print("=== 检查旧集合内容 ===")
    count = await db.student_appointments.count_documents({})
    print(f"student_appointments 集合中有 {count} 条记录")

    if count > 0:
        print("\n旧集合内容:")
        async for doc in db.student_appointments.find():
            print(f"  {doc}")

        print("\n=== 检查新集合是否有相同数据 ===")
        # 检查是否有重复的数据
        async for old_doc in db.student_appointments.find():
            duplicate = await db.appointments.find_one({
                "student_id": old_doc.get("student_id"),
                "course_id": old_doc.get("course_id")
            })
            if duplicate:
                print(f"发现重复数据: student_id={old_doc.get('student_id')}, course_id={old_doc.get('course_id')}")
            else:
                print(f"无重复数据: student_id={old_doc.get('student_id')}, course_id={old_doc.get('course_id')}")

        print("\n=== 删除旧集合 ===")
        # 删除旧集合
        result = await db.student_appointments.drop()
        print("✅ 已成功删除 student_appointments 集合")
    else:
        print("ℹ️  student_appointments 集合已经是空的，无需删除")

    # 验证删除结果
    collections = await db.list_collection_names()
    if "student_appointments" not in collections:
        print("✅ 确认 student_appointments 集合已被删除")
    else:
        print("❌ 删除失败，student_appointments 集合仍然存在")

    print(f"\n当前数据库集合: {collections}")

    client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_old_collection())