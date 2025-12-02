from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date



class StudentModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    nickname: Optional[str] = Field(None, max_length=50, description="别称")
    learning_item: str = Field(..., description="学习项目")
    package_type: str = Field(..., pattern="^(1v1|1v多)$", description="套餐类型")
    total_lessons: int = Field(..., gt=0, description="总课程数")
    remaining_lessons: int = Field(..., ge=0, description="剩余课程数")
    price: int = Field(..., gt=0, description="售价(元)")
    venue_share: int = Field(..., ge=0, description="游泳馆分成(元)")
    profit: int = Field(..., description="利润(元)")
    id_card: Optional[str] = Field(None, max_length=18, description="身份证号码")
    phone: Optional[str] = Field(None, max_length=11, description="手机号码")
    note: Optional[str] = Field(None, max_length=500, description="备注")
    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    nickname: Optional[str] = Field(None, max_length=50)
    learning_item: str = Field(...)
    package_type: str = Field(..., pattern="^(1v1|1v多)$")
    total_lessons: int = Field(..., gt=0)
    price: int = Field(..., gt=0)
    venue_share: int = Field(..., ge=0)
    id_card: Optional[str] = Field(None, max_length=18)
    phone: Optional[str] = Field(None, max_length=11)
    note: Optional[str] = Field(None, max_length=500)

class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    nickname: Optional[str] = Field(None, max_length=50)
    learning_item: Optional[str] = Field(None)
    id_card: Optional[str] = Field(None, max_length=18)
    phone: Optional[str] = Field(None, max_length=11)
    note: Optional[str] = Field(None, max_length=500)

class AppointmentModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    student_id: str = Field(..., description="学员ID")
    appointment_date: date = Field(..., description="预约日期")
    time_slot: str = Field(..., pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$", description="时间段")
    status: str = Field(default="scheduled", pattern="^(scheduled|checked|absent)$", description="预约状态")
    create_time: datetime = Field(default_factory=datetime.utcnow)
    update_time: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}

class AppointmentCreate(BaseModel):
    student_id: str = Field(..., description="学员ID")
    appointment_date: str = Field(...)  # 接受字符串格式，在service中转换
    time_slot: str = Field(..., pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[date] = Field(None)
    time_slot: Optional[str] = Field(None, pattern="^([01]?[0-9]|2[0-3]):[0-5][0-9]$")

class AttendanceModel(BaseModel):
    id: Optional[str] = Field(alias="_id", default=None)
    student_id: str = Field(..., description="学员ID")
    appointment_id: str = Field(..., description="预约ID")
    attendance_date: date = Field(..., description="上课日期")
    time_slot: str = Field(..., description="时间段")
    status: str = Field(..., pattern="^(checked|absent)$", description="出勤状态")
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