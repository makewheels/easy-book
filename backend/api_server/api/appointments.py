from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import date, datetime
from api_server.models import AppointmentModel, AppointmentCreate, AppointmentUpdate
from api_server.services import AppointmentService

router = APIRouter()

@router.post("/")
async def create_appointment(appointment: AppointmentCreate):
    try:
        appointment_data = appointment.dict()
        created_appointment = await AppointmentService.create(appointment_data)
        return {
            "code": 200,
            "message": "预约创建成功",
            "data": created_appointment.dict()
        }
    except ValueError as e:
        return {
            "code": 400,
            "message": str(e),
            "data": None
        }
    except Exception as e:
        # 处理 MongoDB 重复键错误
        error_str = str(e)
        if "E11000 duplicate key error" in error_str and "student_id_1_appointment_date_1_time_slot_1" in error_str:
            return {
                "code": 400,
                "message": "该时间段已有预约，请选择其他时间",
                "data": None
            }
        return {
            "code": 500,
            "message": str(e),
            "data": None
        }

@router.get("/student/{student_id}", response_model=List[AppointmentModel])
async def get_student_appointments(
    student_id: str,
    future_only: bool = Query(False, description="只获取未来预约")
):
    try:
        appointments = await AppointmentService.get_by_student(student_id, future_only)
        return appointments
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily/{target_date}")
async def get_daily_appointments(target_date: date):
    try:
        daily_data = await AppointmentService.get_daily(target_date)
        return {
            "code": 200,
            "message": "获取成功",
            "data": daily_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{appointment_id}", response_model=AppointmentModel)
async def update_appointment(appointment_id: str, appointment_update: AppointmentUpdate):
    try:
        update_data = appointment_update.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供更新数据")
        
        updated_appointment = await AppointmentService.update(appointment_id, update_data)
        if not updated_appointment:
            raise HTTPException(status_code=404, detail="预约不存在")
        return updated_appointment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{appointment_id}")
async def delete_appointment(appointment_id: str):
    try:
        success = await AppointmentService.delete(appointment_id)
        if not success:
            raise HTTPException(status_code=404, detail="预约不存在")
        return {"message": "预约删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))