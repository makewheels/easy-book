import asyncio
from pymongo import ASCENDING, DESCENDING
from motor.motor_asyncio import AsyncIOMotorClient

async def compare_collections():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.easy_book

    print("=== student_appointments 集合内容 ===")
    async for doc in db.student_appointments.find():
        print(f"  {doc}")

    print("\n=== appointments 集合内容 ===")
    async for doc in db.appointments.find():
        print(f"  {doc}")

    # 检查是否应该删除旧的集合
    print("\n=== 分析 ===")
    student_appointments_count = await db.student_appointments.count_documents({})
    appointments_count = await db.appointments.count_documents({})

    print(f"student_appointments: {student_appointments_count} 条记录")
    print(f"appointments: {appointments_count} 条记录")

    if student_appointments_count == 0:
        print("✅ 可以安全删除 student_appointments 集合")
    elif appointments_count == 0:
        print("❌ 新集合 appointments 为空，不能删除 student_appointments")
    else:
        print("⚠️  两个集合都有数据，需要手动检查")

    client.close()

if __name__ == "__main__":
    asyncio.run(compare_collections())