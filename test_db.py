import asyncio
import sys
sys.path.append('backend')

from api_server.database import get_database

async def test():
    db = get_database()
    appointments = await db.get_appointments()
    print('预约状态检查:')
    for apt in appointments:
        print(f'预约ID: {apt.get("_id")}, 状态: {apt.get("status")}, 学生ID: {apt.get("student_id")}')

if __name__ == "__main__":
    asyncio.run(test())