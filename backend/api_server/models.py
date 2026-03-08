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
            'fields': [('title', ASCENDING)],
            'name': 'idx_title',
            'background': True,
        },
    ]

    @classmethod
    def get_collection_name(cls) -> str:
        return "courses"


class MongoDBPackageModel(MongoDBBaseModel):
    """套餐MongoDB模型"""

    # 索引配置
    indexes = [
        {
            'fields': [('student_id', ASCENDING)],
            'name': 'idx_student_id',
            'background': True,
        },
        {
            'fields': [('package_type', ASCENDING)],
            'name': 'idx_package_type',
            'background': True,
        },
        {
            'fields': [('create_time', DESCENDING)],
            'name': 'idx_create_time_desc',
            'background': True,
        },
        {
            'fields': [('student_id', ASCENDING), ('create_time', DESCENDING)],
            'name': 'idx_student_time_desc',
            'background': True,
        },
    ]

    @classmethod
    def get_collection_name(cls) -> str:
        return "packages"


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
    phone: Optional[str] = Field(None, max_length=20, description="电话号码")
    learning_item: str = Field(..., description="学习项目")
    notes: Optional[str] = Field(None, max_length=500, description="备注")
    remaining_lessons: Optional[int] = Field(None, description="剩余课时(从套餐聚合)")
    total_lessons: Optional[int] = Field(None, description="总课时(从套餐聚合)")
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default_factory=datetime.now)

    
class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    learning_item: str = Field(...)
    notes: Optional[str] = Field(None, max_length=500)

class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    learning_item: Optional[str] = Field(None)
    notes: Optional[str] = Field(None, max_length=500)

class AppointmentModel(BaseModel):
    id: Optional[str] = None
    student_id: str = Field(..., description="学员ID")
    start_time: datetime = Field(..., description="课程开始时间")
    end_time: Optional[datetime] = Field(None, description="课程结束时间（由服务端计算）")
    duration_in_minutes: Optional[int] = Field(None, gt=0, description="课程时长（分钟）")
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
    title: str = Field(..., description="课程标题（格式：(人数)学生名）")
    start_time: datetime = Field(..., description="课程开始时间")
    end_time: datetime = Field(..., description="课程结束时间")
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

    
class CourseCreate(BaseModel):
    title: str = Field(..., description="课程标题")
    start_time: datetime = Field(..., description="课程开始时间")
    end_time: datetime = Field(..., description="课程结束时间")

class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, description="课程标题")

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


class DailyAppointmentResponse(BaseModel):
    date: str
    weekday: str
    is_past: bool
    slots: list


# 套餐相关模型
class PackageModel(BaseModel):
    id: Optional[str] = None
    student_id: str = Field(..., description="学员ID")
    name: str = Field(..., min_length=1, max_length=100, description="套餐名称")

    # 统一的套餐类型字段：count_based(记次) | time_based(时长) | 1v1, 1v2, 1v3, 1v5等
    package_type: str = Field(..., description="套餐类型：count_based, time_based, 1v1, 1v2, 1v3, 1v5等")

    # 价格信息（使用小数）
    price: float = Field(..., gt=0, description="售价(元)")
    venue_share: float = Field(..., ge=0, description="上交俱乐部(元)")

    # 记次套餐详情
    count_based_info: Optional[dict] = Field(None, description="记次套餐信息：{total_lessons: int, remaining_lessons: int}")

    # 时长套餐详情
    time_based_info: Optional[dict] = Field(None, description="时长套餐信息：{start_date: str, end_date: str}")

    create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    update_time: datetime = Field(default_factory=datetime.now, description="更新时间")

    @property
    def is_package_valid(self) -> bool:
        """检查套餐是否有效"""
        if not self.is_active:
            return False

        if self.package_category == "count_based":
            return (self.remaining_lessons or 0) > 0
        else:  # time_based
            if self.unlimited_access:
                return True
            if not self.package_end_date:
                return True
            return date.today() <= self.package_end_date

    @property
    def package_status_text(self) -> str:
        """获取套餐状态文本"""
        if not self.is_active:
            return "已停用"

        if self.package_category == "count_based":
            remaining = self.remaining_lessons or 0
            total = self.total_lessons or 0
            return f"{remaining}/{total}节"
        else:  # time_based
            if self.unlimited_access:
                return "永久有效"
            if not self.package_end_date:
                return "未设置有效期"
            today = date.today()
            if today > self.package_end_date:
                return "已过期"
            days_left = (self.package_end_date - today).days
            if days_left <= 7:
                return f"{days_left}天后过期"
            else:
                return self.package_end_date.strftime("%Y-%m-%d到期")

    @property
    def package_type_display(self) -> str:
        """获取套餐类型显示文本"""
        type_map = {
            "1v1": "一对一",
            "1v2": "一对二",
            "1v3": "一对三",
            "1v5": "一对五",
            "1v多": "一对多",
            "time_based": "时长套餐"
        }
        return type_map.get(self.package_type, self.package_type)


class PackageCreate(BaseModel):
    student_id: str = Field(..., description="学员ID")
    name: str = Field(..., min_length=1, max_length=100, description="套餐名称")

    # 统一的套餐类型字段：count_based, time_based, 1v1, 1v2, 1v3, 1v5等
    package_type: str = Field(..., description="套餐类型")

    # 价格信息（使用小数）
    price: float = Field(..., gt=0, description="售价(元)")
    venue_share: float = Field(..., ge=0, description="上交俱乐部(元)")

    # 记次套餐详情
    count_based_info: Optional[dict] = Field(None, description="记次套餐信息：{total_lessons: int, remaining_lessons: int}")

    # 时长套餐详情
    time_based_info: Optional[dict] = Field(None, description="时长套餐信息：{start_date: str, end_date: str}")


class PackageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    package_type: Optional[str] = Field(None)
    price: Optional[float] = Field(None, gt=0)
    venue_share: Optional[float] = Field(None, ge=0)
    count_based_info: Optional[dict] = Field(None, description="记次套餐信息：{total_lessons: int, remaining_lessons: int}")
    time_based_info: Optional[dict] = Field(None, description="时长套餐信息：{start_date: str, end_date: str}")


# 考勤相关模型
class AttendanceModel(BaseModel):
    id: Optional[str] = None
    student_id: str = Field(..., description="学员ID")
    appointment_id: str = Field(..., description="预约ID")
    attendance_date: Optional[str] = Field(None, description="考勤日期")
    time_slot: Optional[str] = Field(None, description="时间段")
    status: str = Field(default="checked", description="状态: checked/cancel")
    lessons_before: int = Field(default=0, description="签到前剩余课时")
    lessons_after: int = Field(default=0, description="签到后剩余课时")
    create_time: Optional[datetime] = Field(default_factory=datetime.now)

class AttendanceCreate(BaseModel):
    appointment_id: str = Field(..., description="预约ID")
    student_id: str = Field(..., description="学员ID")