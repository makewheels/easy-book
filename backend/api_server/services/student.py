"""
学员服务模块
处理学员相关的业务逻辑，包括创建、查询、更新、删除学员信息
"""

from typing import List, Optional
from api_server.models import StudentModel
from api_server.database import get_database


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

        # 计算利润
        profit = student_data["price"] - student_data["venue_share"]
        student_data["profit"] = profit
        student_data["remaining_lessons"] = student_data["total_lessons"]

        student_id = await db.create_student(student_data)
        student_data["_id"] = student_id
        student_data["id"] = student_id

        return StudentModel(**student_data)

    @staticmethod
    def _prepare_student_data(student_data: dict) -> dict:
        """
        为学员数据提供默认值

        Args:
            student_data: 原始学员数据

        Returns:
            处理后的学员数据
        """
        if student_data.get('remaining_lessons') is None:
            student_data['remaining_lessons'] = student_data.get('total_lessons', 0)

        if student_data.get('profit') is None:
            student_data['profit'] = student_data.get('price', 0) - student_data.get('venue_share', 0)

        return student_data

    @staticmethod
    async def get_all(skip: int = 0, limit: int = 20) -> List[StudentModel]:
        """
        获取所有学员列表

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            学员对象列表
        """
        db = get_database()
        students = await db.get_students()
        # 简单分页
        students = students[skip:skip+limit]
        processed_students = []
        for student in students:
            student = StudentService._prepare_student_data(student.copy())
            processed_students.append(StudentModel(**student))
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
            student = StudentService._prepare_student_data(student)
            return StudentModel(**student)
        return None

    @staticmethod
    async def update(student_id: str, update_data: dict) -> Optional[StudentModel]:
        """
        更新学员信息

        Args:
            student_id: 学员ID
            update_data: 更新的数据

        Returns:
            更新后的学员对象，如果更新失败则返回None
        """
        db = get_database()
        success = await db.update_student(student_id, update_data)
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