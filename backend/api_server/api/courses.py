from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import date, datetime
from api_server.models import CourseModel, CourseCreate, CourseUpdate
from api_server.services import CourseService

router = APIRouter()

@router.post("/")
async def create_course(course: CourseCreate):
    try:
        created_course = await CourseService.create_course(course.dict())
        return {
            "code": 200,
            "message": "课程创建成功",
            "data": created_course.dict()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{course_id}", response_model=CourseModel)
async def get_course(course_id: str):
    try:
        course = await CourseService.get_course_by_id(course_id)
        if course:
            return course
        else:
            raise HTTPException(status_code=404, detail="Course not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{course_id}", response_model=CourseModel)
async def update_course(course_id: str, course_update: CourseUpdate):
    try:
        update_data = course_update.dict(exclude_unset=True)
        updated_course = await CourseService.update_course(course_id, update_data)
        if updated_course:
            return updated_course
        else:
            raise HTTPException(status_code=404, detail="Course not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/daily/{date_str}")
async def get_daily_courses(date_str: str):
    try:
        # 解析日期
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        target_datetime = datetime.combine(target_date, datetime.min.time())

        courses = await CourseService.get_daily_courses(target_datetime)
        return {
            "code": 200,
            "message": "获取成功",
            "data": [course.dict() for course in courses]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail="日期格式无效，请使用YYYY-MM-DD格式")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/range")
async def get_courses_by_range(
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)")
):
    try:
        # 解析日期
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        courses = await CourseService.get_courses_by_date_range(start_dt, end_dt)
        return {
            "code": 200,
            "message": "获取成功",
            "data": [course.dict() for course in courses]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail="日期格式无效，请使用YYYY-MM-DD格式")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))