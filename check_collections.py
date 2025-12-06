import asyncio
from pymongo import ASCENDING, DESCENDING
from motor.motor_asyncio import AsyncIOMotorClient

async def check_collections():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.easy_book

    # 获取所有集合名称
    collections = await db.list_collection_names()
    print("数据库中的所有集合:")
    for collection in collections:
        count = await db[collection].count_documents({})
        print(f"  - {collection}: {count} 条记录")

    # 检查appointments集合的内容
    if "appointments" in collections:
        print("\nappointments集合内容:")
        async for doc in db.appointments.find().limit(3):
            print(f"  {doc}")

    # 检查是否有其他类似的集合
    similar_collections = [c for c in collections if 'appoint' in c.lower() or 'stu' in c.lower()]
    print(f"\n包含'appoint'或'stu'的集合: {similar_collections}")

    client.close()

if __name__ == "__main__":
    asyncio.run(check_collections())