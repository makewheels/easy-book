"""
考勤服务模块
处理考勤相关的业务逻辑，包括签到、取消、查询考勤记录等
"""

from typing import List
from datetime import datetime, date
from api_server.models import StudentModel, AppointmentModel, AttendanceModel
from api_server.database import get_database


class AttendanceService:
    """考勤服务类"""

    @staticmethod
    async def checkin(appointment_id: str, student_id: str) -> AttendanceModel:
        """
        学员签到

        Args:
            appointment_id: 预约ID
            student_id: 学员ID

        Returns:
            创建的考勤记录对象
        """
        db = get_database()

        # 获取学员和预约信息
        student = await db.get_student(student_id)
        appointment = await db.get_appointment(appointment_id)

        if not student:
            raise ValueError("学员不存在")
        if not appointment:
            raise ValueError("预约不存在")

        # 处理可能缺失的字段
        remaining_lessons = student.get("remaining_lessons", student.get("total_lessons", 0))
        if remaining_lessons <= 0:
            raise ValueError("剩余课程不足")
        if appointment.get("status") != "scheduled":
            raise ValueError("预约状态无效")

        # 检查是否已经签到
        attendances = await db.get_attendances()
        for att in attendances:
            if att.get("appointment_id") == appointment_id:
                raise ValueError("已经签到过了")

        # 获取时间信息（支持新旧格式）
        start_time = appointment.get("start_time")
        attendance_date = None
        time_slot = None

        if start_time:
            # 新格式：从 start_time 提取日期和时间
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            attendance_date = start_time.date()
            time_slot = start_time.strftime("%H:%M")
        else:
            # 旧格式：使用 appointment_date 和 time_slot
            appointment_date_str = appointment.get("appointment_date")
            if appointment_date_str:
                attendance_date = date.fromisoformat(appointment_date_str)
            time_slot = appointment.get("time_slot", "")

        # 创建上课记录
        attendance_data = {
            "student_id": student_id,
            "appointment_id": appointment_id,
            "attendance_date": attendance_date.isoformat() if attendance_date else "",
            "time_slot": time_slot,
            "status": "checked",
            "lessons_before": remaining_lessons,
            "lessons_after": remaining_lessons - 1,
            "create_time": datetime.now()
        }

        # 插入上课记录
        await db.create_attendance(attendance_data)

        # 更新学员剩余课程
        await db.update_student(student_id, {"remaining_lessons": remaining_lessons - 1})

        # 更新预约状态
        await db.update_appointment(appointment_id, {"status": "checked", "update_time": datetime.now()})

        attendance_data["_id"] = attendance_data.get("id", "")
        return AttendanceModel(**attendance_data)

    @staticmethod
    async def mark_cancel(appointment_id: str, student_id: str) -> AttendanceModel:
        """
        标记预约为取消状态

        Args:
            appointment_id: 预约ID
            student_id: 学员ID

        Returns:
            创建的考勤记录对象
        """
        db = get_database()

        # 获取预约信息
        appointment = await db.get_appointment(appointment_id)
        if not appointment:
            raise ValueError("预约不存在")

        # 获取学员信息
        student = await db.get_student(student_id)
        if not student:
            raise ValueError("学员不存在")

        # 处理可能缺失的字段
        remaining_lessons = student.get("remaining_lessons", student.get("total_lessons", 0))

        # 检查是否已经有考勤记录
        attendances = await db.get_attendances()
        for att in attendances:
            if att.get("appointment_id") == appointment_id and att.get("student_id") == student_id:
                raise ValueError("已经标记过考勤了")

        # 获取时间信息（支持新旧格式）
        start_time = appointment.get("start_time")
        attendance_date = None
        time_slot = None

        if start_time:
            # 新格式：从 start_time 提取日期和时间
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            attendance_date = start_time.date()
            time_slot = start_time.strftime("%H:%M")
        else:
            # 旧格式：使用 appointment_date 和 time_slot
            appointment_date_str = appointment.get("appointment_date")
            if appointment_date_str:
                attendance_date = date.fromisoformat(appointment_date_str)
            time_slot = appointment.get("time_slot", "")

        # 创建上课记录
        attendance_data = {
            "student_id": student_id,
            "appointment_id": appointment_id,
            "attendance_date": attendance_date.isoformat() if attendance_date else "",
            "time_slot": time_slot,
            "status": "cancel",
            "lessons_before": remaining_lessons,
            "lessons_after": remaining_lessons,
            "create_time": datetime.now()
        }

        # 更新预约状态
        await db.update_appointment(appointment_id, {"status": "cancel", "update_time": datetime.now()})

        # 插入考勤记录
        await db.create_attendance(attendance_data)

        attendance_data["_id"] = attendance_data.get("id", "")
        return AttendanceModel(**attendance_data)

    @staticmethod
    async def get_by_student(student_id: str) -> List[AttendanceModel]:
        """
        获取学员的所有考勤记录

        Args:
            student_id: 学员ID

        Returns:
            考勤记录对象列表，按日期降序排列
        """
        db = get_database()
        attendances = await db.get_student_attendances(student_id)

        # 按日期排序
        attendances.sort(key=lambda x: x.get("attendance_date", ""), reverse=True)
        return [AttendanceModel(**att) for att in attendances]