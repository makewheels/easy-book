"""
学生预约服务模块
处理学生预约相关的业务逻辑，包括预约创建、取消、签到等
"""

from typing import List, Optional
from datetime import datetime, timedelta, date
from api_server.models import StudentAppointmentModel, StudentAppointmentCreate, StudentAppointmentUpdate
from api_server.database import get_database
from .course import CourseService
from .student import StudentService


class AppointmentService:
    """学生预约服务类"""

    @staticmethod
    async def create_appointment(appointment_data: dict) -> StudentAppointmentModel:
        """
        创建学生预约

        Args:
            appointment_data: 预约数据字典，必须包含 student_id, start_time, end_time

        Returns:
            创建的预约对象
        """
        db = get_database()

        # 验证必需字段
        required_fields = ["student_id", "start_time", "end_time"]
        for field in required_fields:
            if field not in appointment_data:
                raise ValueError(f"缺少必需字段: {field}")

        student_id = appointment_data["student_id"]
        start_time = appointment_data["start_time"]
        end_time = appointment_data["end_time"]

        # 验证学生存在
        student = await db.get_student(student_id)
        if not student:
            raise ValueError("学生不存在")

        # 检查学生时间冲突
        has_conflict = await db.check_student_time_conflict(student_id, start_time, end_time)
        if has_conflict:
            raise ValueError("学生在该时间段已有预约")

        # 查找或创建课程
        course = await CourseService.find_or_create_course(start_time, end_time)
        if not course:
            raise ValueError("无法创建或获取课程")

        # 创建学生预约
        appointment_record = {
            "student_id": student_id,
            "course_id": course.id,
            "status": "scheduled",
            "lesson_consumed": False
        }

        appointment_id = await db.create_student_appointment(appointment_record)

        # 获取创建的预约
        appointment = await db.get_appointment(appointment_id)
        if not appointment:
            raise ValueError("预约创建失败")

        # 更新课程标题（(人数)学生名）
        await CourseService.update_course_title(course.id)

        return StudentAppointmentModel(**appointment)

    @staticmethod
    async def get_appointment_by_id(appointment_id: str) -> Optional[StudentAppointmentModel]:
        """
        根据ID获取预约信息

        Args:
            appointment_id: 预约ID

        Returns:
            预约对象，如果不存在则返回None
        """
        db = get_database()
        appointment = await db.get_appointment(appointment_id)
        if not appointment:
            return None
        # 附带课程信息
        course_id = appointment.get("course_id")
        if course_id:
            course = await db.get_course(course_id)
            if course:
                appointment["course"] = course
        return StudentAppointmentModel(**appointment)

    @staticmethod
    async def cancel_appointment(appointment_id: str) -> bool:
        """
        取消预约（直接删除预约记录）

        Args:
            appointment_id: 预约ID

        Returns:
            取消是否成功
        """
        db = get_database()

        target_appointment = await db.get_appointment(appointment_id)
        if not target_appointment:
            raise ValueError("预约不存在")

        if target_appointment.get("status") in ("cancelled", "cancel"):
            raise ValueError("预约已取消")

        success = await db.delete_appointment(appointment_id)

        if success:
            # 课程标题随学员变化刷新
            course_id = target_appointment.get("course_id")
            if course_id:
                await CourseService.update_course_title(course_id)

        return success

    @staticmethod
    async def checkin_appointment(appointment_id: str) -> bool:
        """
        预约签到（仅改状态，课时扣减在考勤模块完成）

        Args:
            appointment_id: 预约ID

        Returns:
            签到是否成功
        """
        db = get_database()

        target_appointment = await db.get_appointment(appointment_id)
        if not target_appointment:
            raise ValueError("预约不存在")

        # 检查预约状态
        if target_appointment.get("status") != "scheduled":
            raise ValueError("只能为待上课的预约签到")

        if target_appointment.get("lesson_consumed", False):
            raise ValueError("该预约已签到")

        # 获取学生信息
        student_id = target_appointment.get("student_id")
        student = await db.get_student(student_id)
        if not student:
            raise ValueError("学生不存在")

        # 更新预约状态
        success = await db.update_appointment(appointment_id, {
            "status": "completed",
            "lesson_consumed": True,
            "update_time": datetime.now()
        })

        return success

    @staticmethod
    async def get_student_appointments(student_id: str, status: Optional[str] = None) -> List[StudentAppointmentModel]:
        """
        获取学生的预约列表

        Args:
            student_id: 学生ID
            status: 预约状态过滤

        Returns:
            预约对象列表，按创建时间倒序排列（最新的在最上面）
        """
        db = get_database()
        appointments = await db.get_appointments(student_id, status)

        # 为每个预约添加课程信息
        result_appointments = []
        for apt in appointments:
            # 获取课程信息
            course_id = apt.get("course_id")
            if course_id:
                course = await db.get_course(course_id)
                if course:
                    apt["course"] = course

            result_appointments.append(StudentAppointmentModel(**apt))

        # 按课程开始时间倒序（没有课程信息时退回创建时间）
        def _sort_key(apt: StudentAppointmentModel):
            course = apt.course or {}
            start = course.get("start_time") or apt.create_time
            if isinstance(start, str):
                try:
                    start = datetime.fromisoformat(start)
                except ValueError:
                    start = apt.create_time
            return start

        result_appointments.sort(key=_sort_key, reverse=True)

        return result_appointments

    @staticmethod
    async def get_course_appointments(course_id: str) -> List[StudentAppointmentModel]:
        """
        获取课程的所有预约

        Args:
            course_id: 课程ID

        Returns:
            预约对象列表
        """
        db = get_database()
        appointments = await db.get_course_appointments(course_id)

        # 为每个预约添加学生信息
        result_appointments = []
        for apt in appointments:
            # 获取学生信息
            student_id = apt.get("student_id")
            if student_id:
                student = await db.get_student(student_id)
                if student:
                    apt["student"] = student

            result_appointments.append(StudentAppointmentModel(**apt))

        return result_appointments

    @staticmethod
    async def get_daily_appointments(date: datetime) -> List[dict]:
        """
        获取指定日期的所有预约（用于日历显示）

        Args:
            date: 日期

        Returns:
            按时间分组的预约数据
        """
        db = get_database()
        # 获取当天的课程
        courses = await CourseService.get_daily_courses(date)

        # 为每个课程获取预约
        time_slots = {}
        for course in courses:
            # 格式化时间为 "HH:MM"
            time_str = course.start_time.strftime("%H:%M")

            # 获取该课程的所有预约
            appointments = await AppointmentService.get_course_appointments(course.id)

            # 筛选活跃预约
            active_appointments = [
                apt for apt in appointments
                if apt.status not in ["cancelled", "no_show"]
            ]

            if active_appointments:
                students = []
                for apt in active_appointments:
                    # 通过 student_id 获取学生信息
                    student_info = await db.get_student(apt.student_id)
                    if student_info:
                        # 从套餐聚合课时与类型（学员文档本身不存课时）
                        packages = await db.get_student_packages(apt.student_id)
                        remaining = sum(
                            (p.get("count_based_info") or {}).get("remaining_lessons", 0)
                            for p in packages
                        )
                        package_types = [
                            p.get("package_type") for p in packages
                            if p.get("package_type") and p.get("package_type") != "time_based"
                        ]
                        student_data = {
                            "id": apt.id,
                            "name": student_info.get("name", ""),
                            "package_type": package_types[0] if package_types else "",
                            "remaining_lessons": remaining,
                            "appointment_id": apt.id,
                            "student_id": apt.student_id,
                            "status": apt.status
                        }
                        students.append(student_data)

                time_slots[time_str] = {
                    "time": time_str,
                    "course_id": course.id,
                    "course_title": course.title,
                    "students": students
                }

        # 转换为数组并按时间排序
        sorted_slots = sorted(time_slots.values(), key=lambda x: x["time"])
        return sorted_slots

    @staticmethod
    async def get_batch_appointments(start_date: date, end_date: date) -> dict:
        """
        批量获取指定时间范围内的所有预约数据

        Args:
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            按日期分组的预约数据字典，格式与单个get_daily_appointments兼容
        """
        batch_data = {}
        weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            weekday = weekday_map[current_date.weekday()]
            is_past = current_date < datetime.now().date()
            current_datetime = datetime.combine(current_date, datetime.min.time())

            try:
                # 获取当天的预约数据
                time_slots = await AppointmentService.get_daily_appointments(current_datetime)

                # 格式化数据，保持与原有API兼容
                batch_data[date_str] = {
                    "date": date_str,
                    "weekday": weekday,
                    "is_past": is_past,
                    "slots": time_slots
                }
            except Exception as e:
                print(f"获取{date_str}的预约数据失败: {e}")
                # 即使某天数据获取失败，也返回空数据，避免中断整个批量请求
                batch_data[date_str] = {
                    "date": date_str,
                    "weekday": weekday,
                    "is_past": is_past,
                    "slots": []
                }

            current_date += timedelta(days=1)

        return batch_data