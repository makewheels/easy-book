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
    async def checkin(appointment_id: str, student_id: str) -> AttendanceModel:  # noqa: C901, PLR0912
        """
        学员签到 — 从有效记次套餐中扣减课时
        """
        db = get_database()

        student = await db.get_student(student_id)
        appointment = await db.get_appointment(appointment_id)

        if not student:
            raise ValueError("学员不存在")
        if not appointment:
            raise ValueError("预约不存在")
        if appointment.get("status") not in ("scheduled", None):
            raise ValueError("预约状态无效")

        # 检查是否已经签到
        attendances = await db.get_attendances()
        for att in attendances:
            if att.get("appointment_id") == appointment_id:
                raise ValueError("已经签到过了")

        # 从套餐聚合剩余课时，选第一个还有余量的记次套餐扣减
        packages = await db.get_student_packages(student_id)
        active_package = None
        remaining_lessons = 0
        for pkg in packages:
            cbi = pkg.get("count_based_info") or {}
            if cbi.get("remaining_lessons", 0) > 0:
                active_package = pkg
                remaining_lessons = cbi.get("remaining_lessons", 0)
                break

        if not active_package or remaining_lessons <= 0:
            raise ValueError("剩余课程不足，请先为学员购买/充值套餐")

        # 获取时间信息（优先预约自带，其次从关联课程取）
        start_time = appointment.get("start_time")
        if not start_time and appointment.get("course_id"):
            course = await db.get_course(appointment.get("course_id"))
            if course:
                start_time = course.get("start_time")
        attendance_date = None
        time_slot = None

        if start_time:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            attendance_date = start_time.date()
            time_slot = start_time.strftime("%H:%M")
        else:
            appointment_date_str = appointment.get("appointment_date")
            if appointment_date_str:
                attendance_date = date.fromisoformat(appointment_date_str)
            time_slot = appointment.get("time_slot", "")

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

        await db.create_attendance(attendance_data)

        # 扣减套餐课时
        new_cbi = (active_package.get("count_based_info") or {}).copy()
        new_cbi["remaining_lessons"] = remaining_lessons - 1
        await db.update_package_by_id(active_package["id"], {
            "count_based_info": new_cbi,
        })

        # 更新预约状态
        await db.update_appointment(appointment_id, {"status": "checked", "lesson_consumed": True})

        attendance_data["id"] = attendance_data.get("id", "")
        return AttendanceModel(**attendance_data)

    @staticmethod
    async def mark_cancel(appointment_id: str, student_id: str) -> AttendanceModel:
        """
        标记预约为取消状态（不扣课时）
        """
        db = get_database()

        appointment = await db.get_appointment(appointment_id)
        if not appointment:
            raise ValueError("预约不存在")

        student = await db.get_student(student_id)
        if not student:
            raise ValueError("学员不存在")

        # 检查是否已有考勤记录
        attendances = await db.get_attendances()
        for att in attendances:
            if att.get("appointment_id") == appointment_id and att.get("student_id") == student_id:
                raise ValueError("已经标记过考勤了")

        # 聚合当前剩余课时（仅用于记录）
        packages = await db.get_student_packages(student_id)
        remaining_lessons = sum(
            (p.get("count_based_info") or {}).get("remaining_lessons", 0)
            for p in packages if p.get("count_based_info")
        )

        # 获取时间信息（优先预约自带，其次从关联课程取）
        start_time = appointment.get("start_time")
        if not start_time and appointment.get("course_id"):
            course = await db.get_course(appointment.get("course_id"))
            if course:
                start_time = course.get("start_time")
        attendance_date = None
        time_slot = None

        if start_time:
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            attendance_date = start_time.date()
            time_slot = start_time.strftime("%H:%M")
        else:
            appointment_date_str = appointment.get("appointment_date")
            if appointment_date_str:
                attendance_date = date.fromisoformat(appointment_date_str)
            time_slot = appointment.get("time_slot", "")

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

        await db.update_appointment(appointment_id, {"status": "cancel", "update_time": datetime.now()})
        await db.create_attendance(attendance_data)

        attendance_data["id"] = attendance_data.get("id", "")
        return AttendanceModel(**attendance_data)

    @staticmethod
    async def get_by_student(student_id: str) -> List[AttendanceModel]:
        """获取学员的所有考勤记录"""
        db = get_database()
        attendances = await db.get_student_attendances(student_id)
        attendances.sort(key=lambda x: x.get("attendance_date", ""), reverse=True)
        return [AttendanceModel(**att) for att in attendances]