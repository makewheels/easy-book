"""
套餐管理API
处理套餐的创建、查询、更新、删除、课时调整等操作

套餐结构（新 schema）：
- package_type: count_based(记次) | time_based(时长) | 1v1/1v2/1v3/1v5(记次的细分类型)
- price / venue_share: 售价与上交俱乐部金额，教练利润 = price - venue_share
- count_based_info: {total_lessons, remaining_lessons}
- time_based_info: {start_date, end_date}
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from pymongo import DESCENDING

from api_server.models import (
    PackageModel, PackageCreate, PackageUpdate,
    MongoDBPackageModel
)
from api_server.mongo_database import db as mongo_db

router = APIRouter(tags=["packages"])


def _collection():
    return mongo_db.db[MongoDBPackageModel.get_collection_name()]


def _doc_to_model(doc: dict) -> PackageModel:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    doc.pop("id_", None)
    return PackageModel(**doc)


class LessonAdjust(BaseModel):
    """课时调整请求（正数=加次数，负数=扣次数）"""
    delta: int = Field(..., description="变化量，正数为增加，负数为减少，例如 +5 / -1")
    adjust_total: bool = Field(default=False, description="是否同时调整总课时（默认只调剩余课时）")
    reason: Optional[str] = Field(default=None, max_length=200, description="调整原因（记录用）")


@router.post("/", response_model=PackageModel, status_code=201)
async def create_package(package_data: PackageCreate):
    """创建新套餐（为学员购买/续费）"""
    try:
        package_dict = package_data.model_dump()
        package_dict["create_time"] = datetime.now()
        package_dict["update_time"] = datetime.now()

        # 记次套餐未显式给 remaining_lessons 时，默认与总课时相同
        if package_dict.get("package_type") != "time_based":
            cbi = package_dict.get("count_based_info") or {}
            if "remaining_lessons" not in cbi and "total_lessons" in cbi:
                cbi["remaining_lessons"] = cbi["total_lessons"]
                package_dict["count_based_info"] = cbi

        insert_result = await _collection().insert_one(package_dict)
        created_package = await _collection().find_one({"_id": insert_result.inserted_id})
        if not created_package:
            raise HTTPException(status_code=500, detail="创建套餐后无法获取数据")
        return _doc_to_model(created_package)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建套餐失败: {str(e)}")


@router.get("/", response_model=List[PackageModel])
async def get_packages(
    student_id: Optional[str] = Query(None, description="学员ID"),
    package_type: Optional[str] = Query(None, description="套餐类型：count_based/time_based/1v1/1v2等"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="返回数量")
):
    """获取套餐列表"""
    try:
        query = {}
        if student_id:
            query["student_id"] = student_id
        if package_type:
            query["package_type"] = package_type

        cursor = _collection().find(query).sort("create_time", DESCENDING).skip(skip).limit(limit)

        packages = []
        async for package in cursor:
            packages.append(_doc_to_model(package))
        return packages

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取套餐列表失败: {str(e)}")


# 注意：/student/{student_id} 必须注册在 /{package_id} 之前，避免被动态路由吞掉
@router.get("/student/{student_id}", response_model=List[PackageModel])
async def get_student_packages(student_id: str):
    """获取指定学员的套餐列表"""
    try:
        cursor = _collection().find({"student_id": student_id}).sort("create_time", DESCENDING)
        packages = []
        async for package in cursor:
            packages.append(_doc_to_model(package))
        return packages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学员套餐列表失败: {str(e)}")


async def _find_package_or_404(package_id: str) -> dict:
    package = await mongo_db.get_package_by_id(package_id)
    if not package:
        raise HTTPException(status_code=404, detail="套餐不存在")
    return package


@router.get("/{package_id}", response_model=PackageModel)
async def get_package(package_id: str):
    """获取单个套餐详情"""
    try:
        package = await _find_package_or_404(package_id)
        return PackageModel(**package)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取套餐详情失败: {str(e)}")


@router.put("/{package_id}", response_model=PackageModel)
async def update_package(package_id: str, package_data: PackageUpdate):
    """更新套餐信息（含财务分成 venue_share、价格、课时等）"""
    try:
        await _find_package_or_404(package_id)

        update_data = package_data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供更新数据")

        success = await mongo_db.update_package_by_id(package_id, update_data)
        if not success:
            raise HTTPException(status_code=400, detail="更新套餐失败")

        updated_package = await mongo_db.get_package_by_id(package_id)
        return PackageModel(**updated_package)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新套餐失败: {str(e)}")


@router.delete("/{package_id}", status_code=204)
async def delete_package(package_id: str):
    """删除套餐"""
    try:
        await _find_package_or_404(package_id)
        # 兼容 ObjectId 与字符串 _id
        from bson import ObjectId
        try:
            result = await _collection().delete_one({"_id": ObjectId(package_id)})
        except Exception:
            result = await _collection().delete_one({"_id": package_id})
        if result.deleted_count == 0:
            result = await _collection().delete_one({"_id": package_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="删除套餐失败")
        return
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除套餐失败: {str(e)}")


@router.post("/{package_id}/adjust-lessons")
async def adjust_lessons(package_id: str, adjust: LessonAdjust):
    """
    调整记次套餐课时（给学员加次数/扣次数）

    delta 为正数表示增加（如续费赠送），负数表示减少。
    """
    try:
        package = await _find_package_or_404(package_id)

        if package.get("package_type") == "time_based":
            raise HTTPException(status_code=400, detail="时长套餐没有课时数，无法调整")

        cbi = dict(package.get("count_based_info") or {})
        remaining = cbi.get("remaining_lessons", 0)
        total = cbi.get("total_lessons", 0)

        new_remaining = remaining + adjust.delta
        if new_remaining < 0:
            raise HTTPException(
                status_code=400,
                detail=f"剩余课时不足：当前 {remaining} 节，不能减少 {abs(adjust.delta)} 节"
            )

        cbi["remaining_lessons"] = new_remaining
        if adjust.adjust_total:
            new_total = total + adjust.delta
            cbi["total_lessons"] = max(new_total, new_remaining)

        success = await mongo_db.update_package_by_id(package_id, {"count_based_info": cbi})
        if not success:
            raise HTTPException(status_code=400, detail="调整课时失败")

        return {
            "message": f"课时调整成功：{remaining} → {new_remaining}",
            "package_id": package_id,
            "student_id": package.get("student_id"),
            "lessons_before": remaining,
            "lessons_after": new_remaining,
            "total_lessons": cbi.get("total_lessons"),
            "delta": adjust.delta,
            "reason": adjust.reason,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调整课时失败: {str(e)}")


@router.post("/{package_id}/consume-lesson")
async def consume_lesson(package_id: str):
    """消耗一节课时（仅适用于记次套餐；签到场景请走考勤接口）"""
    try:
        package = await _find_package_or_404(package_id)

        if package.get("package_type") == "time_based":
            raise HTTPException(status_code=400, detail="只有记次套餐可以消耗课程")

        cbi = package.get("count_based_info") or {}
        remaining_lessons = cbi.get("remaining_lessons", 0)
        if remaining_lessons <= 0:
            raise HTTPException(status_code=400, detail="课程已用完")

        new_cbi = dict(cbi)
        new_cbi["remaining_lessons"] = remaining_lessons - 1
        success = await mongo_db.update_package_by_id(package_id, {"count_based_info": new_cbi})
        if not success:
            raise HTTPException(status_code=400, detail="消耗课程失败")

        return {
            "message": "课程消耗成功",
            "remaining_lessons": remaining_lessons - 1
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"消耗课程失败: {str(e)}")


@router.get("/{package_id}/status")
async def get_package_status(package_id: str):
    """获取套餐状态信息"""
    try:
        package = await _find_package_or_404(package_id)
        package_model = PackageModel(**package)

        return {
            "is_valid": package_model.is_package_valid,
            "status_text": package_model.package_status_text,
            "package_type": package_model.package_type,
            "package_type_display": package_model.package_type_display,
            "price": package_model.price,
            "venue_share": package_model.venue_share,
            "coach_profit": round(package_model.price - package_model.venue_share, 2),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取套餐状态失败: {str(e)}")
