from fastapi import APIRouter, HTTPException, Query
from typing import List
from api_server.models import StudentModel, StudentCreate, StudentUpdate
from api_server.services import StudentService
from api_server.database import get_database

router = APIRouter()

@router.post("/", response_model=StudentModel)
async def create_student(student: StudentCreate):
    try:
        student_data = student.dict()
        created_student = await StudentService.create(student_data)
        return created_student
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[StudentModel])
async def get_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    try:
        students = await StudentService.get_all(skip=skip, limit=limit)
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{student_id}", response_model=StudentModel)
async def get_student(student_id: str):
    try:
        student = await StudentService.get_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="学员不存在")
        return student
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{student_id}", response_model=StudentModel)
async def update_student(student_id: str, student_update: StudentUpdate):
    try:
        update_data = student_update.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供更新数据")
        
        updated_student = await StudentService.update(student_id, update_data)
        if not updated_student:
            raise HTTPException(status_code=404, detail="学员不存在")
        return updated_student
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{student_id}")
async def delete_student(student_id: str):
    try:
        success = await StudentService.delete(student_id)
        if not success:
            raise HTTPException(status_code=404, detail="学员不存在")
        return {"message": "学员删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))