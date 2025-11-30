from fastapi import APIRouter, HTTPException
from api_server.models import AttendanceModel, AttendanceCreate
from api_server.services import AttendanceService

router = APIRouter()

@router.post("/checkin")
async def checkin(attendance: AttendanceCreate):
    try:
        print(f"收到签到请求: appointment_id={attendance.appointment_id}, student_id={attendance.student_id}")
        attendance_record = await AttendanceService.checkin(
            attendance.appointment_id,
            attendance.student_id
        )
        return {
            "code": 200,
            "message": "签到成功",
            "data": {
                "attendance_id": str(attendance_record.id),
                "student_id": str(attendance_record.student_id),
                "lessons_before": attendance_record.lessons_before,
                "lessons_after": attendance_record.lessons_after,
                "message": f"签到成功，剩余课程：{attendance_record.lessons_after}"
            }
        }
    except ValueError as e:
        print(f"签到验证错误: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"签到系统错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/absent")
async def mark_absent(attendance: AttendanceCreate):
    try:
        print(f"收到缺席请求: appointment_id={attendance.appointment_id}, student_id={attendance.student_id}")
        attendance_record = await AttendanceService.mark_absent(
            attendance.appointment_id,
            attendance.student_id
        )
        return {
            "code": 200,
            "message": "标记缺席成功",
            "data": {
                "attendance_id": str(attendance_record.id),
                "student_id": str(attendance_record.student_id),
                "lessons_before": attendance_record.lessons_before,
                "lessons_after": attendance_record.lessons_after,
                "message": "已标记为缺席"
            }
        }
    except ValueError as e:
        print(f"缺席验证错误: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"缺席系统错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/student/{student_id}")
async def get_student_attendance(student_id: str):
    try:
        attendances = await AttendanceService.get_by_student(student_id)
        attendance_list = []
        for att in attendances:
            attendance_list.append({
                "id": str(att.id),
                "date": att.attendance_date.strftime("%Y-%m-%d"),
                "time": att.time_slot,
                "status": att.status,
                "lessons_before": att.lessons_before,
                "lessons_after": att.lessons_after
            })
        
        return {
            "code": 200,
            "message": "获取成功",
            "data": attendance_list
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))