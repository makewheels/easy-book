"""
学员服务模块
处理学员相关的业务逻辑，包括创建、查询、更新、删除学员信息
"""

from typing import List, Optional
from api_server.models import StudentModel
from api_server.database import get_database


def map_mongo_to_api(mongo_doc: dict) -> dict:
    """将MongoDB文档映射为API响应格式"""
    api_doc = mongo_doc.copy()
    # 检查_id或id字段，统一转换为id字段
    if '_id' in api_doc:
        api_doc['id'] = str(api_doc['_id'])
        del api_doc['_id']
    elif 'id' in api_doc:
        # id字段已经存在，确保是字符串格式
        api_doc['id'] = str(api_doc['id'])
    return api_doc


def map_api_to_mongo(api_doc: dict) -> dict:
    """将API请求数据映射为MongoDB格式"""
    mongo_doc = api_doc.copy()
    if 'id' in mongo_doc:
        mongo_doc['_id'] = mongo_doc['id']
        del mongo_doc['id']
    return mongo_doc


class StudentService:
    """学员服务类"""

    @staticmethod
    async def create(student_data: dict) -> StudentModel:
        """
        创建新学员

        Args:
            student_data: 学员数据字典

        Returns:
            创建的学员对象
        """
        db = get_database()

        student_id = await db.create_student(student_data)
        student_data["_id"] = student_id
        student_data["id"] = student_id

        # 映射为API格式
        api_data = map_mongo_to_api(student_data)
        return StudentModel(**api_data)

    
    @staticmethod
    async def get_all(skip: int = 0, limit: int = 100) -> List[StudentModel]:
        """
        获取所有学员列表（按创建时间降序）

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            学员对象列表
        """
        from datetime import datetime

        db = get_database()
        students = await db.get_students()

        # 简化排序逻辑：按创建时间降序（新学生在前）
        def get_sort_key(student):
            create_time_str = student.get("create_time", "")
            try:
                if create_time_str:
                    create_time = datetime.fromisoformat(create_time_str.replace('Z', '+00:00'))
                    create_timestamp = create_time.timestamp()
                else:
                    create_timestamp = 0
            except:
                create_timestamp = 0
            # 用负数让新学生排在前面
            return -create_timestamp

        # 按排序键进行排序
        students.sort(key=get_sort_key)

        # 分页
        students = students[skip:skip+limit]
        processed_students = []
        for student in students:
            student_copy = student.copy()
            # 映射为API格式
            api_data = map_mongo_to_api(student_copy)
            processed_students.append(StudentModel(**api_data))
        return processed_students

    @staticmethod
    async def get_by_id(student_id: str) -> Optional[StudentModel]:
        """
        根据ID获取学员信息

        Args:
            student_id: 学员ID

        Returns:
            学员对象，如果不存在则返回None
        """
        db = get_database()
        student = await db.get_student(student_id)
        if student:
            # 映射为API格式
            api_data = map_mongo_to_api(student)
            return StudentModel(**api_data)
        return None

    @staticmethod
    async def update(student_id: str, update_data: dict) -> Optional[StudentModel]:
        """
        更新学员信息

        Args:
            student_id: 学员ID（标准id）
            update_data: 更新的数据

        Returns:
            更新后的学员对象，如果更新失败则返回None
        """
        db = get_database()
        # 将标准id映射为MongoDB的_id进行查询
        mongo_student_id = student_id
        success = await db.update_student(mongo_student_id, update_data)
        if success:
            return await StudentService.get_by_id(student_id)
        return None

    @staticmethod
    async def delete(student_id: str) -> bool:
        """
        删除学员

        Args:
            student_id: 学员ID

        Returns:
            删除是否成功
        """
        db = get_database()
        return await db.delete_student(student_id)

    @staticmethod
    async def update_lessons(student_id: str, new_lessons: int) -> bool:
        """
        更新学员剩余课程数量

        Args:
            student_id: 学员ID
            new_lessons: 新的剩余课程数量

        Returns:
            更新是否成功
        """
        db = get_database()
        return await db.update_student(student_id, {"remaining_lessons": new_lessons})