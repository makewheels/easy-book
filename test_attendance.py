import asyncio
import sys
sys.path.append('backend')

from api_server.database import get_database

async def test():
    db = get_database()
    attendances = await db.get_attendances()
    print('考勤记录检查:')
    for att in attendances:
        print(f'考勤ID: {att.get("_id")}, 预约ID: {att.get("appointment_id")}, 状态: {att.get("status")}')

if __name__ == "__main__":
    asyncio.run(test())