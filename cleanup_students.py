#!/usr/bin/env python3
import asyncio
import sys
import os

# 添加backend目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api_server.mongo_database import get_database

async def cleanup_students():
    db = get_database()
    await db.connect()

    # 保留的学员ID列表
    keep_student_ids = [
        "692f0f558a3ca1ece733a064",  # 马文华
        "692bd06358ba9900a7ac5b67",  # 许志玲
        "692c0d612e3567ee406e053a"   # 李文华
    ]

    print("保留的学员:")
    for student_id in keep_student_ids:
        student = await db.get_student(student_id)
        if student:
            print(f"  - {student.get('name')} (ID: {student_id})")
        else:
            print(f"  - 学员ID {student_id} 不存在")

    # 获取所有学员
    all_students = []
    async for student in db.db.students.find():
        all_students.append(student)

    print(f"\n总共找到 {len(all_students)} 个学员")
    print(f"保留 {len(keep_student_ids)} 个学员，删除 {len(all_students) - len(keep_student_ids)} 个学员")

    # 删除不需要保留的学员
    deleted_count = 0
    for student in all_students:
        student_id = str(student['_id'])
        if student_id not in keep_student_ids:
            # 删除学员及其相关预约和考勤记录
            success = await db.delete_student(student_id)
            if success:
                deleted_count += 1
                print(f"已删除学员: {student.get('name')} (ID: {student_id})")
            else:
                print(f"删除失败: {student.get('name')} (ID: {student_id})")

    print(f"\n成功删除 {deleted_count} 个学员")

    # 再次检查剩余学员
    print("\n剩余学员:")
    remaining_students = []
    async for student in db.db.students.find():
        remaining_students.append(student)
        print(f"  - {student.get('name')} (ID: {str(student['_id'])})")

    print(f"\n总共剩余 {len(remaining_students)} 个学员")

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(cleanup_students())