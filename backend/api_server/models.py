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



class MongoDBCourseModel(MongoDBBaseModel):
    """课程MongoDB模型"""

    # 索引配置
    indexes = [
        {
            'fields': [('start_time', ASCENDING)],
            'name': 'idx_start_time',
            'background': True,
        },
        {
            'fields': [('end_time', ASCENDING)],
            'name': 'idx_end_time',
            'background': True,
        },
        {
            'fields': [('start_time', ASCENDING), ('end_time', ASCENDING)],
            'name': 'idx_time_range',
            'background': True,
        },
        {
            'fields': [('status', ASCENDING)],
            'name': 'idx_status',
            'background': True,
        },
        {
            'fields': [('title', ASCENDING)],
            'name': 'idx_title',
            'background': True,
        },
    ]

    @classmethod
    def get_collection_name(cls) -> str:
        return "courses"


class MongoDBAppointmentModel(MongoDBBaseModel):
    """预约MongoDB模型"""

    # 索引配置
    indexes = [
        {
            'fields': [('student_id', ASCENDING)],
            'name': 'idx_student_id',
            'background': True,
        },
        {
            'fields': [('course_id', ASCENDING)],
            'name': 'idx_course_id',
            'background': True,
        },
        {
            'fields': [('student_id', ASCENDING), ('course_id', ASCENDING)],
            'name': 'idx_student_course',
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




# Pydantic模型类 - 用于API数据验证和序列化
class StudentModel(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    learning_item: str = Field(..., description="学习项目")

    # 套餐类型系统
    package_category: str = Field(default="count_based", pattern="^(count_based|time_based)$", description="套餐类别：count_based(记次) | time_based(记时)")
    original_package_type: str = Field(..., pattern="^(1v1|1v多)$", description="原套餐类型(1v1|1v多)")
    package_duration_type: Optional[str] = Field(None, pattern="^(monthly|quarterly|yearly|custom)$", description="时长套餐类型")
    package_end_date: Optional[datetime] = Field(None, description="套餐到期时间(仅time_based使用)")
    package_duration_days: Optional[int] = Field(None, gt=0, description="自定义天数(仅custom类型使用)")
    unlimited_access: bool = Field(default=False, description="是否无限制上课(仅time_based使用)")

    # 兼容老数据的字段
    package_type: str = Field(..., description="套餐类型(兼容老数据)")
    total_lessons: Optional[int] = Field(None, gt=0, description="总课程数(仅count_based使用)")
    remaining_lessons: Optional[int] = Field(None, ge=0, description="剩余课程数(仅count_based使用)")

    price: int = Field(..., gt=0, description="售价(元)")
    venue_share: int = Field(..., ge=0, description="上交俱乐部(元)")
    profit: Optional[int] = Field(None, description="利润(元)")
    note: Optional[str] = Field(None, max_length=500, description="备注")
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default_factory=datetime.now)

    @property
    def is_package_valid(self) -> bool:
        """检查套餐是否有效"""
        if self.package_category == "count_based":
            return self.remaining_lessons > 0 if self.remaining_lessons else True
        else:  # time_based
            if not self.package_end_date:
                return True
            return datetime.now() <= self.package_end_date

    @property
    def package_status_text(self) -> str:
        """获取套餐状态文本"""
        if self.package_category == "count_based":
            remaining = self.remaining_lessons or 0
            total = self.total_lessons or 0
            return f"{remaining}/{total}次"
        else:  # time_based
            if not self.package_end_date:
                return "永久有效"
            days_left = (self.package_end_date - datetime.now()).days
            if days_left <= 0:
                return "已过期"
            elif days_left <= 30:
                return f"{days_left}天后过期"
            else:
                return self.package_end_date.strftime("%Y/%m/%d到期")

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    learning_item: str = Field(...)

    # 套餐类型系统
    package_category: str = Field(default="count_based", pattern="^(count_based|time_based)$", description="套餐类别")
    original_package_type: str = Field(..., pattern="^(1v1|1v多)$", description="原套餐类型")
    package_duration_type: Optional[str] = Field(None, pattern="^(monthly|quarterly|yearly|custom)$", description="时长套餐类型")
    package_duration_days: Optional[int] = Field(None, gt=0, description="自定义天数")
    unlimited_access: bool = Field(default=False, description="无限制上课")

    # 兼容老数据
    total_lessons: Optional[int] = Field(None, gt=0, description="总课程数(仅count_based)")
    price: int = Field(..., gt=0)
    venue_share: int = Field(..., ge=0)
    note: Optional[str] = Field(None, max_length=500)

    def validate_package_data(self):
        """验证套餐数据的完整性"""
        if self.package_category == "count_based":
            if not self.total_lessons or self.total_lessons <= 0:
                raise ValueError("记次套餐必须设置总课程数")
        else:  # time_based
            if self.package_duration_type == "custom":
                if not self.package_duration_days or self.package_duration_days <= 0:
                    raise ValueError("自定义时长套餐必须设置天数")
            elif self.package_duration_type and not self.unlimited_access:
                # 预设类型的套餐，系统会自动计算结束时间
                pass

class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    learning_item: Optional[str] = Field(None)
    note: Optional[str] = Field(None, max_length=500)

class AppointmentModel(BaseModel):
    id: Optional[str] = None
    student_id: str = Field(..., description="学员ID")
    start_time: datetime = Field(..., description="课程开始时间")
    end_time: Optional[datetime] = Field(None, description="课程结束时间（由服务端计算）")
    duration_in_minutes: Optional[int] = Field(None, gt=0, description="课程时长（分钟）")
    status: str = Field(default="scheduled", pattern="^(scheduled|checked|cancel)$", description="预约状态")
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default_factory=datetime.now)

    @property
    def duration_minutes(self) -> int:
        """获取课程时长（分钟）"""
        return self.duration_in_minutes

    @property
    def duration_hours(self) -> float:
        """获取课程时长（小时）"""
        return round(self.duration_in_minutes / 60, 2)

class AppointmentCreate(BaseModel):
    student_id: str = Field(..., description="学员ID")
    start_time: datetime = Field(..., description="课程开始时间")
    duration_in_minutes: int = Field(..., gt=0, description="课程时长（分钟）")

    model_config = {"populate_by_name": True}

# 课程相关模型
class CourseModel(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., description="课程标题")
    start_time: datetime = Field(..., description="课程开始时间")
    end_time: datetime = Field(..., description="课程结束时间")
    max_students: int = Field(default=6, gt=0, description="最大学生数")
    current_students: int = Field(default=0, ge=0, description="当前学生数")
    status: str = Field(default="scheduled", pattern="^(scheduled|completed|cancelled)$", description="课程状态")
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default_factory=datetime.now)

    @property
    def duration_minutes(self) -> int:
        """获取课程时长（分钟）"""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    @property
    def duration_hours(self) -> float:
        """获取课程时长（小时）"""
        return round(self.duration_minutes / 60, 2)

    @property
    def is_available(self) -> bool:
        """检查课程是否可预约"""
        return self.current_students < self.max_students and self.status == "scheduled"

class CourseCreate(BaseModel):
    title: str = Field(..., description="课程标题")
    start_time: datetime = Field(..., description="课程开始时间")
    end_time: datetime = Field(..., description="课程结束时间")
    max_students: int = Field(default=6, gt=0, description="最大学生数")

class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, description="课程标题")
    max_students: Optional[int] = Field(None, gt=0, description="最大学生数")
    status: Optional[str] = Field(None, pattern="^(scheduled|completed|cancelled)$", description="课程状态")

# 学生预约相关模型
class StudentAppointmentModel(BaseModel):
    id: Optional[str] = None
    student_id: str = Field(..., description="学生ID")
    course_id: str = Field(..., description="课程ID")
    status: str = Field(default="scheduled", pattern="^(scheduled|completed|cancelled|no_show)$", description="预约状态")
    lesson_consumed: bool = Field(default=False, description="是否已消耗课程")
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default_factory=datetime.now)

class StudentAppointmentCreate(BaseModel):
    student_id: str = Field(..., description="学生ID")
    course_id: str = Field(..., description="课程ID")

class StudentAppointmentUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(scheduled|completed|cancelled|no_show)$", description="预约状态")
    lesson_consumed: Optional[bool] = Field(None, description="是否已消耗课程")

class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = Field(None, description="课程开始时间")
    duration_in_minutes: Optional[int] = Field(None, gt=0, description="课程时长（分钟）")
    status: Optional[str] = Field(None, pattern="^(scheduled|checked|cancel)$", description="预约状态")


class DailyAppointmentResponse(BaseModel):
    date: str
    weekday: str
    is_past: bool
    slots: list