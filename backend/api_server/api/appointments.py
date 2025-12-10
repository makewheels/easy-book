from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import date, datetime, timedelta
from api_server.models import (
    StudentAppointmentModel,
    StudentAppointmentCreate,
    StudentAppointmentUpdate
)
from api_server.services import AppointmentService

router = APIRouter()

@router.post("/")
async def create_student_appointment(appointment: dict):
    """
    创建学生预约
    支持原始的预约格式，内部转换为新的三表架构
    """
    try:
        # 验证必需字段
        required_fields = ["student_id", "start_time", "duration_in_minutes"]
        for field in required_fields:
            if field not in appointment:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")

        # 计算结束时间
        start_time = appointment["start_time"]
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))

        duration_in_minutes = appointment["duration_in_minutes"]
        end_time = start_time + timedelta(minutes=duration_in_minutes)

        # 构建预约数据
        appointment_data = {
            "student_id": appointment["student_id"],
            "start_time": start_time,
            "end_time": end_time
        }

        created_appointment = await AppointmentService.create_appointment(appointment_data)

        # 安全地获取数据
        if hasattr(created_appointment, 'dict'):
            appointment_dict = created_appointment.dict()
        elif isinstance(created_appointment, dict):
            appointment_dict = created_appointment
        else:
            appointment_dict = str(created_appointment)

        return {
            "code": 200,
            "message": "预约创建成功",
            "data": appointment_dict
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()  # 保留错误堆栈用于生产环境调试
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch")
async def get_batch_appointments(
    start_date: str = Query(..., description="开始日期，格式：YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期，格式：YYYY-MM-DD")
):
    """
    批量获取指定时间范围内的所有预约数据
    用于日历页面初始化，减少网络请求次数
    """
    try:
        # 解析日期
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

        if start_date_obj > end_date_obj:
            raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

        # 限制查询范围，避免查询过多数据
        max_days = 90  # 最多查询90天
        days_diff = (end_date_obj - start_date_obj).days + 1
        if days_diff > max_days:
            raise HTTPException(status_code=400, detail=f"查询范围不能超过{max_days}天")

        # 批量获取数据
        batch_data = await AppointmentService.get_batch_appointments(start_date_obj, end_date_obj)

        return {
            "code": 200,
            "message": "获取成功",
            "data": batch_data
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"日期格式无效，请使用YYYY-MM-DD格式: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{appointment_id}", response_model=StudentAppointmentModel)
async def get_student_appointment(appointment_id: str):
    try:
        appointment = await AppointmentService.get_appointment_by_id(appointment_id)
        if appointment:
            return appointment
        else:
            raise HTTPException(status_code=404, detail="Appointment not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{appointment_id}", response_model=StudentAppointmentModel)
async def update_student_appointment(appointment_id: str, appointment_update: StudentAppointmentUpdate):
    try:
        update_data = appointment_update.dict(exclude_unset=True)
        # 注意：这里简化了更新逻辑，因为主要的状态更新通过专门的接口处理

        # 对于这种API，我们主要支持状态更新
        if "status" in update_data:
            # 这里需要调用相应的服务方法来处理状态变更
            pass

        # 获取更新后的预约
        updated_appointment = await AppointmentService.get_appointment_by_id(appointment_id)
        if updated_appointment:
            return updated_appointment
        else:
            raise HTTPException(status_code=404, detail="Appointment not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{appointment_id}")
async def delete_student_appointment(appointment_id: str):
    try:
        success = await AppointmentService.cancel_appointment(appointment_id)
        if success:
            return {
                "code": 200,
                "message": "预约取消成功",
                "data": None
            }
        else:
            raise HTTPException(status_code=404, detail="Appointment not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{appointment_id}/cancel")
async def cancel_appointment(appointment_id: str):
    """
    取消预约（专用接口）
    """
    try:
        success = await AppointmentService.cancel_appointment(appointment_id)
        if success:
            return {
                "code": 200,
                "message": "预约取消成功",
                "data": None
            }
        else:
            return {
                "code": 400,
                "message": "预约取消失败",
                "data": None
            }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{appointment_id}/checkin")
async def checkin_appointment(appointment_id: str):
    """
    学员签到
    """
    try:
        success = await AppointmentService.checkin_appointment(appointment_id)
        if success:
            return {
                "code": 200,
                "message": "签到成功",
                "data": None
            }
        else:
            return {
                "code": 400,
                "message": "签到失败",
                "data": None
            }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/student/{student_id}")
async def get_student_appointments(
    student_id: str,
    status: Optional[str] = Query(None, description="预约状态过滤")
):
    try:
        appointments = await AppointmentService.get_student_appointments(student_id, status)
        return {
            "code": 200,
            "message": "获取成功",
            "data": [apt.dict() for apt in appointments]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/course/{course_id}")
async def get_course_appointments(course_id: str):
    try:
        appointments = await AppointmentService.get_course_appointments(course_id)
        return {
            "code": 200,
            "message": "获取成功",
            "data": [apt.dict() for apt in appointments]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily/{date_str}")
async def get_daily_appointments(date_str: str):
    """
    获取指定日期的预约（用于日历显示）
    兼容原有的appointments接口格式
    """
    try:
        # 解析日期
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        target_datetime = datetime.combine(target_date, datetime.min.time())

        # 获取当天的预约
        time_slots = await AppointmentService.get_daily_appointments(target_datetime)

        # 格式化返回数据，保持与原有API兼容
        weekday_map = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekday_map[target_date.weekday()]
        is_past = target_date < datetime.now().date()

        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "date": date_str,
                "weekday": weekday,
                "is_past": is_past,
                "slots": time_slots
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail="日期格式无效，请使用YYYY-MM-DD格式")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))