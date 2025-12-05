"""
预约服务模块
处理预约相关的业务逻辑，包括创建、查询、更新、取消预约等
"""

from typing import List, Optional, Union
from datetime import datetime, date, timedelta
from api_server.models import StudentModel, AppointmentModel
from api_server.database import get_database
from .utils import convert_legacy_time_data, calculate_dynamic_status_new, calculate_dynamic_status


class AppointmentService:
    """预约服务类"""

    @staticmethod
    async def create(appointment_data: dict) -> AppointmentModel:
        """
        创建新预约

        Args:
            appointment_data: 预约数据字典

        Returns:
            创建的预约对象
        """
        db = get_database()

        # 处理新旧格式的时间数据
        if "start_time" in appointment_data and "end_time" in appointment_data:
            # 新格式：使用 start_time 和 end_time
            start_time = appointment_data["start_time"]
            end_time = appointment_data["end_time"]

            # 验证时间格式
            if not isinstance(start_time, datetime):
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                    appointment_data["start_time"] = start_time
                else:
                    raise ValueError("start_time 格式错误")

            if not isinstance(end_time, datetime):
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time)
                    appointment_data["end_time"] = end_time
                else:
                    raise ValueError("end_time 格式错误")

            # 验证时间逻辑
            if start_time >= end_time:
                raise ValueError("开始时间必须早于结束时间")

            # 检查时间冲突（新格式）
            await AppointmentService.check_time_conflict(
                appointment_data["student_id"],
                start_time,
                end_time
            )

            # 为了兼容性，同时保存旧格式字段
            appointment_data["appointment_date"] = start_time.date().isoformat()
            appointment_data["time_slot"] = start_time.strftime("%H:%M")

        else:
            # 旧格式：使用 appointment_date 和 time_slot
            appointment_date = appointment_data["appointment_date"]
            time_slot = appointment_data["time_slot"]

            # 处理日期格式（确保统一存储为字符串）
            if isinstance(appointment_date, date):
                appointment_data["appointment_date"] = appointment_date.isoformat()

            # 检查时间冲突（旧格式）
            await AppointmentService.check_conflict(
                appointment_data["student_id"],
                appointment_date,
                time_slot
            )

            # 转换为新格式
            appointment_data = convert_legacy_time_data(appointment_data)

        # 获取学员信息，检查剩余课程
        student = await db.get_student(appointment_data["student_id"])
        if not student:
            raise ValueError("学员不存在")

        remaining_lessons = student.get("remaining_lessons", 0)
        if remaining_lessons <= 0:
            raise ValueError("学员剩余课程不足，无法预约")

        # 扣减课程次数
        new_remaining_lessons = remaining_lessons - 1
        await db.update_student(appointment_data["student_id"], {
            "remaining_lessons": new_remaining_lessons,
            "update_time": datetime.utcnow()
        })

        # 设置创建和更新时间
        appointment_data["create_time"] = datetime.utcnow()
        appointment_data["update_time"] = datetime.utcnow()

        # 创建预约
        appointment_id = await db.create_appointment(appointment_data)
        appointment_data["_id"] = appointment_id
        appointment_data["id"] = appointment_id

        return AppointmentModel(**appointment_data)

    @staticmethod
    async def check_time_conflict(student_id: str, start_time: datetime, end_time: datetime):
        """
        检查新格式的时间冲突

        Args:
            student_id: 学员ID
            start_time: 开始时间
            end_time: 结束时间
        """
        db = get_database()

        # 获取学员在该时间段的所有预约
        appointments = await db.get_student_appointments(student_id)

        for appointment in appointments:
            if appointment.get("status") == "cancel":
                continue

            # 获取现有预约的开始和结束时间
            if "start_time" in appointment and "end_time" in appointment:
                existing_start = appointment["start_time"]
                existing_end = appointment["end_time"]

                # 处理字符串格式的时间
                if isinstance(existing_start, str):
                    existing_start = datetime.fromisoformat(existing_start)
                if isinstance(existing_end, str):
                    existing_end = datetime.fromisoformat(existing_end)

                # 检查时间重叠
                if not (end_time <= existing_start or start_time >= existing_end):
                    raise ValueError(f"该时间段已存在预约冲突")

    @staticmethod
    async def check_conflict(student_id: str, appointment_date: str, time_slot: str):
        """
        检查旧格式的时间冲突

        Args:
            student_id: 学员ID
            appointment_date: 预约日期
            time_slot: 时间段
        """
        db = get_database()

        # 检查是否已有相同时间的预约
        existing_appointments = await db.get_appointments_by_date_and_student(
            appointment_date, student_id
        )

        for appointment in existing_appointments:
            if appointment.get("time_slot") == time_slot and appointment.get("status") != "cancel":
                raise ValueError("该时间段已存在预约")

    @staticmethod
    async def get_by_id(appointment_id: str) -> Optional[AppointmentModel]:
        """
        根据ID获取预约信息

        Args:
            appointment_id: 预约ID

        Returns:
            预约对象，如果不存在则返回None
        """
        db = get_database()
        appointment = await db.get_appointment(appointment_id)
        if appointment:
            return AppointmentModel(**appointment)
        return None

    @staticmethod
    async def update(appointment_id: str, update_data: dict) -> Optional[AppointmentModel]:
        """
        更新预约信息

        Args:
            appointment_id: 预约ID
            update_data: 更新的数据

        Returns:
            更新后的预约对象，如果更新失败则返回None
        """
        db = get_database()
        update_data["update_time"] = datetime.utcnow()
        success = await db.update_appointment(appointment_id, update_data)
        if success:
            return await AppointmentService.get_by_id(appointment_id)
        return None

    @staticmethod
    async def delete(appointment_id: str) -> bool:
        """
        删除预约

        Args:
            appointment_id: 预约ID

        Returns:
            删除是否成功
        """
        db = get_database()
        return await db.delete_appointment(appointment_id)

    @staticmethod
    async def cancel(appointment_id: str) -> bool:
        """
        取消预约并恢复课程次数

        Args:
            appointment_id: 预约ID

        Returns:
            取消是否成功
        """
        db = get_database()

        # 获取预约信息
        appointment = await db.get_appointment(appointment_id)
        if not appointment:
            raise ValueError("预约不存在")

        # 获取学员信息
        student = await db.get_student(appointment.get("student_id"))
        if not student:
            raise ValueError("学员不存在")

        # 检查预约状态，只有scheduled状态的预约才能取消
        if appointment.get("status") != "scheduled":
            raise ValueError("只能取消待上课的预约")

        # 恢复课程次数
        current_remaining = student.get("remaining_lessons", 0)
        total_lessons = student.get("total_lessons", 0)

        # 确保不超过总课程数
        new_remaining = min(current_remaining + 1, total_lessons)

        # 更新学员剩余课程
        await db.update_student(appointment.get("student_id"), {
            "remaining_lessons": new_remaining,
            "update_time": datetime.utcnow()
        })

        # 更新预约状态为取消
        success = await db.update_appointment(appointment_id, {
            "status": "cancel",
            "update_time": datetime.utcnow()
        })

        return success

    @staticmethod
    async def get_student_appointments(student_id: str, status: Optional[str] = None) -> List[AppointmentModel]:
        """
        获取学员的所有预约

        Args:
            student_id: 学员ID
            status: 预约状态过滤

        Returns:
            预约对象列表
        """
        db = get_database()
        appointments = await db.get_student_appointments(student_id)

        if status:
            appointments = [apt for apt in appointments if apt.get("status") == status]

        return [AppointmentModel(**apt) for apt in appointments]

    @staticmethod
    async def get_upcoming_appointments(days: int = 30) -> List[dict]:
        """
        获取未来指定天数内的预约

        Args:
            days: 未来天数

        Returns:
            预约数据列表
        """
        db = get_database()
        return await db.get_upcoming_appointments(days)

    @staticmethod
    async def get_week_appointments(start_date: date) -> dict:
        """
        获取一周的预约数据

        Args:
            start_date: 周开始日期

        Returns:
            按日期组织的预约数据字典
        """
        db = get_database()
        return await db.get_week_appointments(start_date)

    @staticmethod
    async def get_daily_appointments(appointment_date: str) -> List[dict]:
        """
        获取指定日期的预约

        Args:
            appointment_date: 预约日期

        Returns:
            预约数据列表
        """
        db = get_database()
        return await db.get_daily_appointments(appointment_date)