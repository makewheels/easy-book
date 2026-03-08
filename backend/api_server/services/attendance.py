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

        # 从套餐聚合剩余课时
        packages = await db.get_student_packages(student_id)
        active_package = None
        remaining_lessons = 0
        for pkg in packages:
            cbi = pkg.get("count_based_info")
            if cbi and cbi.get("remaining_lessons", 0) > 0:
                if active_package is None or cbi.get("remaining_lessons", 0) > 0:
                    active_package = pkg
                    remaining_lessons = cbi.get("remaining_lessons", 0)
                    break  # 使用第一个有余量的套餐

        if remaining_lessons <= 0:
            raise ValueError("剩余课程不足")

        # 获取时间信息
        start_time = appointment.get("start_time")
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
        if active_package:
            new_remaining = remaining_lessons - 1
            new_cbi = active_package.get("count_based_info", {}).copy()
            new_cbi["remaining_lessons"] = new_remaining
            pkg_id = active_package.get("id") or active_package.get("_id")
            if pkg_id:
                from bson import ObjectId as BsonObjectId
                # 先尝试 id 字段查询，再尝试 _id + ObjectId
                result = await db.db.packages.update_one(
                    {"id": str(pkg_id)},
                    {"$set": {"count_based_info": new_cbi, "update_time": datetime.now()}}
                )
                if result.modified_count == 0:
                    try:
                        await db.db.packages.update_one(
                            {"_id": BsonObjectId(str(pkg_id))},
                            {"$set": {"count_based_info": new_cbi, "update_time": datetime.now()}}
                        )
                    except Exception:
                        await db.db.packages.update_one(
                            {"_id": str(pkg_id)},
                            {"$set": {"count_based_info": new_cbi, "update_time": datetime.now()}}
                        )

        # 更新预约状态
        await db.update_appointment(appointment_id, {"status": "checked", "update_time": datetime.now()})

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

        # 获取时间信息
        start_time = appointment.get("start_time")
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