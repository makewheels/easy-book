import asyncio
from api_server.database import connect_to_mongo, get_database

async def test_connection():
    try:
        print("正在连接MongoDB...")
        await connect_to_mongo()
        print("MongoDB连接成功!")
        
        # 测试数据库操作
        db = get_database()
        students = await db.get_students()
        print(f"当前学生数量: {len(students)}")
        
        return True
    except Exception as e:
        print(f"连接失败: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())