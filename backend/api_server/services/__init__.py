"""
服务模块统一导出
"""

from .utils import (
    calculate_dynamic_status_new,
    calculate_dynamic_status,
    convert_legacy_time_data
)

from .student import StudentService
from .course import CourseService
from .appointment import AppointmentService

__all__ = [
    # 工具函数
    "calculate_dynamic_status_new",
    "calculate_dynamic_status",
    "convert_legacy_time_data",

    # 服务类
    "StudentService",
    "CourseService",
    "AppointmentService"
]