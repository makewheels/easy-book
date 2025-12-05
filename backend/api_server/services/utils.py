"""
工具函数模块
提供通用的工具函数，主要用于状态计算和数据转换
"""

from typing import Union
from datetime import datetime, date, timedelta


def calculate_dynamic_status_new(start_time: datetime, end_time: datetime, db_status: str) -> str:
    """
    根据当前时间和新的时间结构动态计算状态

    Args:
        start_time: 课程开始时间
        end_time: 课程结束时间
        db_status: 数据库中的状态 (scheduled, checked, cancel)

    Returns:
        动态状态 (scheduled, active, completed, checked, cancel)
    """
    # 如果已经签到或取消，保持原状态
    if db_status in ["checked", "cancel"]:
        return db_status

    # 如果是scheduled状态，需要判断时间
    # 确保使用naive datetime进行比较
    if start_time.tzinfo is not None:
        start_time = start_time.replace(tzinfo=None)
    if end_time.tzinfo is not None:
        end_time = end_time.replace(tzinfo=None)

    now = datetime.now()

    if now < start_time:
        # 还未到上课时间，显示为scheduled（蓝色）
        return "scheduled"
    elif now < end_time:
        # 正在上课时间，显示为active（进行中）
        return "active"
    else:
        # 已经过了上课时间，显示为completed（已完成）
        return "completed"


def calculate_dynamic_status(db_status: str, appointment_date: Union[date, str], time_slot: str) -> str:
    """
    根据当前时间和预约时间动态计算状态（兼容旧版本）

    Args:
        db_status: 数据库中的状态 (scheduled, checked, cancel)
        appointment_date: 预约日期
        time_slot: 时间段 (例如: "10:00")

    Returns:
        动态状态 (scheduled, active, completed, checked, cancel)
    """
    # 如果已经签到或取消，保持原状态
    if db_status in ["checked", "cancel"]:
        return db_status

    # 如果是scheduled状态，需要判断时间
    now = datetime.now()

    # 解析日期
    if isinstance(appointment_date, str):
        try:
            appointment_date_obj = date.fromisoformat(appointment_date)
        except ValueError:
            return db_status
    else:
        appointment_date_obj = appointment_date

    # 解析时间段
    try:
        hour, minute = map(int, time_slot.split(":"))
        appointment_datetime = datetime.combine(appointment_date_obj, datetime.min.time().replace(hour=hour, minute=minute))
    except (ValueError, AttributeError):
        # 如果时间解析失败，返回原状态
        return db_status

    # 判断时间状态
    class_end_time = appointment_datetime + timedelta(hours=1)

    if now < appointment_datetime:
        # 还未到上课时间，显示为scheduled（蓝色）
        return "scheduled"
    elif now < class_end_time:
        # 正在上课时间，显示为active（进行中）
        return "active"
    else:
        # 已经过了上课时间，显示为completed（已完成）
        return "completed"


def convert_legacy_time_data(appointment_data: dict) -> dict:
    """
    转换旧格式的时间数据为新格式

    Args:
        appointment_data: 包含 appointment_date 和 time_slot 的数据

    Returns:
        包含 start_time 和 end_time 的数据
    """
    appointment_date = appointment_data.get("appointment_date")
    time_slot = appointment_data.get("time_slot")

    if not appointment_date or not time_slot:
        return appointment_data

    # 如果已经有 start_time 和 end_time，不需要转换
    if "start_time" in appointment_data and "end_time" in appointment_data:
        return appointment_data

    # 解析日期
    if isinstance(appointment_date, str):
        try:
            appointment_date_obj = date.fromisoformat(appointment_date)
        except ValueError:
            return appointment_data
    else:
        appointment_date_obj = appointment_date

    # 解析时间
    try:
        hour, minute = map(int, time_slot.split(":"))
        start_datetime = datetime.combine(appointment_date_obj, datetime.min.time().replace(hour=hour, minute=minute))
        end_datetime = start_datetime + timedelta(hours=1)  # 默认1小时

        # 添加新字段
        appointment_data["start_time"] = start_datetime
        appointment_data["end_time"] = end_datetime

    except (ValueError, AttributeError):
        pass

    return appointment_data