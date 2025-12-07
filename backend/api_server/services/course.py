"""
课程服务模块
处理课程相关的业务逻辑，包括课程创建、查询、标题更新等
"""

from typing import List, Optional
from datetime import datetime, timedelta
from api_server.models import CourseModel, CourseCreate, CourseUpdate, StudentModel
from api_server.database import get_database


class CourseService:
    """课程服务类"""

    @staticmethod
    async def create_course(course_data: dict) -> CourseModel:
        """
        创建新课程

        Args:
            course_data: 课程数据字典，必须包含 title, start_time, end_time

        Returns:
            创建的课程对象
        """
        db = get_database()

        # 验证必需字段
        required_fields = ["title", "start_time", "end_time"]
        for field in required_fields:
            if field not in course_data:
                raise ValueError(f"缺少必需字段: {field}")

        # 验证时间逻辑
        start_time = course_data["start_time"]
        end_time = course_data["end_time"]
        if start_time >= end_time:
            raise ValueError("结束时间必须晚于开始时间")

        # 检查时间冲突
        existing_course = await db.find_course_by_time(start_time, end_time)
        if existing_course:
            raise ValueError("该时间段已存在课程")

        # 创建课程
        course_id = await db.create_course(course_data)

        # 获取创建的课程
        course = await db.get_course(course_id)
        if course:
            return CourseModel(**course)
        else:
            raise ValueError("课程创建失败")

    @staticmethod
    async def find_or_create_course(start_time: datetime, end_time: datetime) -> CourseModel:
        """
        查找或创建课程（核心业务逻辑）

        Args:
            start_time: 课程开始时间
            end_time: 课程结束时间

        Returns:
            课程对象
        """
        db = get_database()

        # 首先查找现有课程
        existing_course = await db.find_course_by_time(start_time, end_time)

        if existing_course:
            # 如果找到课程，直接返回
            return CourseModel(**existing_course)
        else:
            # 如果没有找到课程，创建新课程
            course_data = {
                "title": "新课程",  # 临时标题，会在添加学生时更新
                "start_time": start_time,
                "end_time": end_time,
                "status": "scheduled"
            }

            return await CourseService.create_course(course_data)

    @staticmethod
    async def update_course_title(course_id: str) -> bool:
        """
        根据当前学生情况更新课程标题

        Args:
            course_id: 课程ID

        Returns:
            更新是否成功
        """
        db = get_database()

        # 获取课程的所有预约
        appointments = await db.get_course_appointments(course_id)

        # 筛选活跃的预约（未取消的）
        active_appointments = [
            apt for apt in appointments
            if apt.get("status") not in ["cancelled", "no_show"]
        ]

        if not active_appointments:
            # 没有学生，使用默认标题
            return await db.update_course(course_id, {"title": "空闲课程"})

        # 获取学生信息
        student_ids = [apt.get("student_id") for apt in active_appointments]
        students = []

        for student_id in student_ids:
            student = await db.get_student(student_id)
            if student:
                students.append(student)

        if not students:
            return await db.update_course(course_id, {"title": "空闲课程"})

        # 生成标题
        if len(students) == 1:
            # 单个学生：使用学生姓名
            title = students[0].get("name", "未知学生")
        else:
            # 多个学生：(N)学生姓名
            title = f"({len(students)}){students[0].get('name', '未知学生')}"

        return await db.update_course(course_id, {"title": title})

    @staticmethod
    async def get_course_by_id(course_id: str) -> Optional[CourseModel]:
        """
        根据ID获取课程

        Args:
            course_id: 课程ID

        Returns:
            课程对象，如果不存在则返回None
        """
        db = get_database()
        course = await db.get_course(course_id)
        if course:
            return CourseModel(**course)
        return None

    @staticmethod
    async def update_course(course_id: str, update_data: dict) -> Optional[CourseModel]:
        """
        更新课程信息

        Args:
            course_id: 课程ID
            update_data: 更新的数据

        Returns:
            更新后的课程对象，如果更新失败则返回None
        """
        db = get_database()
        success = await db.update_course(course_id, update_data)
        if success:
            return await CourseService.get_course_by_id(course_id)
        return None

    @staticmethod
    async def get_courses_by_date_range(start_date: datetime, end_date: datetime) -> List[CourseModel]:
        """
        获取指定日期范围内的课程

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            课程对象列表
        """
        db = get_database()
        courses = await db.get_courses_by_date_range(start_date, end_date)
        return [CourseModel(**course) for course in courses]

    @staticmethod
    async def get_daily_courses(date: datetime) -> List[CourseModel]:
        """
        获取指定日期的课程

        Args:
            date: 日期

        Returns:
            课程对象列表
        """
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        return await CourseService.get_courses_by_date_range(start_of_day, end_of_day)

    