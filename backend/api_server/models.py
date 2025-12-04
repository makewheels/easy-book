from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from api_server.base_model import BaseModel as MongoDBBaseModel
from pymongo import ASCENDING, DESCENDING


# MongoDB模型类 - 用于索引管理和数据库操作
class MongoDBStudentModel(MongoDBBaseModel):
    """学员MongoDB模型"""

    # 索引配置 - 仅用于查询优化，不使用唯一约束
    indexes = [
        {
            'fields': [('name', ASCENDING)],
            'name': 'idx_name',
            'background': True,
        },
        {
            'fields': [('create_time', DESCENDING)],
            'name': 'idx_create_time_desc',
            'background': True,
        },
      ]

    @classmethod
    def get_collection_name(cls) -> str:
        return "students"


class MongoDBAppointmentModel(MongoDBBaseModel):
    """预约MongoDB模型"""

    # 索引配置 - 仅用于查询优化，不使用唯一约束
    indexes = [
        {
            'fields': [('student_id', ASCENDING)],
            'name': 'idx_student_id',
            'background': True,
        },
        {
            'fields': [('appointment_date', ASCENDING)],
            'name': 'idx_appointment_date',
            'background': True,
        },
        {
            'fields': [('appointment_date', ASCENDING), ('time_slot', ASCENDING)],
            'name': 'idx_date_time',
            'background': True,
        },
        {
            'fields': [('status', ASCENDING)],
            'name': 'idx_status',
            'background': True,
        },
    ]

    @classmethod
    def get_collection_name(cls) -> str:
        return "appointments"


class MongoDBAttendanceModel(MongoDBBaseModel):
    """考勤MongoDB模型"""

    # 索引配置 - 仅用于查询优化，不使用唯一约束
    indexes = [
        {
            'fields': [('student_id', ASCENDING)],
            'name': 'idx_student_id',
            'background': True,
        },
        {
            'fields': [('attendance_date', DESCENDING)],
            'name': 'idx_attendance_date_desc',
            'background': True,
        },
        {
            'fields': [('appointment_id', ASCENDING)],
            'name': 'idx_appointment_id',
            'background': True,
        },
        {
            'fields': [('status', ASCENDING)],
            'name': 'idx_status',
            'background': True,
        },
    ]

    @classmethod
    def get_collection_name(cls) -> str:
        return "attendances"


# Pydantic模型类 - 用于API数据验证和序列化
class StudentModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    learning_item: str = Field(..., description="学习项目")
    package_type: str = Field(..., pattern="^(1v1|1v多)$", description="套餐类型")
    total_lessons: int = Field(..., gt=0, description="总课程数")
    remaining_lessons: Optional[int] = Field(None, ge=0, description="剩余课程数")
    price: int = Field(..., gt=0, description="售价(元)")
    venue_share: int = Field(..., ge=0, description="上交俱乐部(元)")
    profit: Optional[int] = Field(None, description="利润(元)")
    note: Optional[str] = Field(None, max_length=500, description="备注")
    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    learning_item: str = Field(...)
    package_type: str = Field(..., pattern="^(1v1|1v多)$")
    total_lessons: int = Field(..., gt=0)
    price: int = Field(..., gt=0)
    venue_share: int = Field(..., ge=0)
    note: Optional[str] = Field(None, max_length=500)

class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    learning_item: Optional[str] = Field(None)
    note: Optional[str] = Field(None, max_length=500)

class AppointmentModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    student_id: str = Field(..., description="学员ID")
    start_time: datetime = Field(..., description="课程开始时间")
    end_time: datetime = Field(..., description="课程结束时间")
    status: str = Field(default="scheduled", pattern="^(scheduled|checked|cancel)$", description="预约状态")
    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)

    # 兼容性字段 - 保留旧字段以便迁移
    appointment_date: Optional[date] = Field(None, description="预约日期（兼容性）")
    time_slot: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="时间段（兼容性）")

    @property
    def duration_minutes(self) -> int:
        """计算课程时长（分钟）"""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    @property
    def duration_hours(self) -> float:
        """计算课程时长（小时）"""
        return round(self.duration_minutes / 60, 2)

    model_config = {"populate_by_name": True}

class AppointmentCreate(BaseModel):
    student_id: str = Field(..., description="学员ID")
    start_time: datetime = Field(..., description="课程开始时间")
    end_time: datetime = Field(..., description="课程结束时间")

    # 兼容性支持 - 允许旧格式数据（完全可选）
    appointment_date: Optional[str] = Field(None, description="预约日期（兼容性）")
    time_slot: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="时间段（兼容性）")

    model_config = {"populate_by_name": True}

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = Field(None)
    time_slot: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")

class AttendanceModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    student_id: str = Field(..., description="学员ID")
    appointment_id: str = Field(..., description="预约ID")
    attendance_date: date = Field(..., description="上课日期")
    time_slot: str = Field(..., description="时间段")
    status: str = Field(..., pattern="^(checked|cancel)$", description="出勤状态")
    lessons_before: int = Field(..., ge=0, description="上课前剩余课程数")
    lessons_after: int = Field(..., ge=0, description="上课后剩余课程数")
    create_time: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}

class AttendanceCreate(BaseModel):
    appointment_id: str = Field(..., description="预约ID")
    student_id: str = Field(..., description="学员ID")

class DailyAppointmentResponse(BaseModel):
    date: str
    weekday: str
    is_past: bool
    slots: list