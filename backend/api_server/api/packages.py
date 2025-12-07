"""
套餐管理API
处理套餐的创建、查询、更新、删除等操作
"""

from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pymongo import DESCENDING
from bson import ObjectId

from api_server.models import (
    PackageModel, PackageCreate, PackageUpdate,
    MongoDBPackageModel
)
from api_server.services.package import PackageService
from api_server.mongo_database import db as mongo_db

router = APIRouter(tags=["packages"])


@router.post("/", response_model=PackageModel, status_code=201)
async def create_package(package_data: PackageCreate):
    """
    创建新套餐
    """
    try:
        # 准备数据库数据
        package_dict = package_data.model_dump()
        package_dict["create_time"] = datetime.now()
        package_dict["update_time"] = datetime.now()

        # 使用MongoDatabase实例创建套餐
        package_id = await mongo_db.db[MongoDBPackageModel.get_collection_name()].insert_one(package_dict)

        # 获取插入的数据
        created_package = await mongo_db.db[MongoDBPackageModel.get_collection_name()].find_one({"_id": package_id.inserted_id})

        # 转换id字段
        if created_package:
            created_package["id"] = str(created_package.pop("_id"))
            return PackageModel(**created_package)
        else:
            raise HTTPException(status_code=500, detail="创建套餐后无法获取数据")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建套餐失败: {str(e)}")


@router.get("/", response_model=List[PackageModel])
async def get_packages(
    student_id: Optional[str] = Query(None, description="学员ID"),
    package_category: Optional[str] = Query(None, description="套餐类别"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="返回数量")
):
    """
    获取套餐列表
    """
    try:
        # 构建查询条件
        query = {}
        if student_id:
            query["student_id"] = student_id
        if package_category:
            query["package_category"] = package_category
        if is_active is not None:
            query["is_active"] = is_active

        # 查询数据
        cursor = mongo_db.db[MongoDBPackageModel.get_collection_name()].find(query).sort("create_time", DESCENDING).skip(skip).limit(limit)

        packages = []
        async for package in cursor:
            package["id"] = str(package.pop("_id"))
            packages.append(PackageModel(**package))

        return packages

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取套餐列表失败: {str(e)}")


@router.get("/{package_id}", response_model=PackageModel)
async def get_package(package_id: str):
    """
    获取单个套餐详情
    """
    try:
        # 验证并转换ObjectId
        try:
            object_id = ObjectId(package_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的套餐ID")

        # 查询数据
        package = await mongo_db.db[MongoDBPackageModel.get_collection_name()].find_one({"_id": object_id})
        if not package:
            raise HTTPException(status_code=404, detail="套餐不存在")

        package["id"] = str(package.pop("_id"))
        return PackageModel(**package)

    except ValueError:
        raise HTTPException(status_code=400, detail="无效的套餐ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取套餐详情失败: {str(e)}")


@router.get("/student/{student_id}", response_model=List[PackageModel])
async def get_student_packages(student_id: str):
    """
    获取指定学员的套餐列表
    """
    try:
        # 构建查询条件
        query = {"student_id": student_id}

        # 查询数据，按创建时间倒序排列
        cursor = mongo_db.db[MongoDBPackageModel.get_collection_name()].find(query).sort("create_time", DESCENDING)

        packages = []
        async for package in cursor:
            package["id"] = str(package.pop("_id"))
            packages.append(PackageModel(**package))

        return packages

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学员套餐列表失败: {str(e)}")


@router.put("/{package_id}", response_model=PackageModel)
async def update_package(package_id: str, package_data: PackageUpdate):
    """
    更新套餐信息
    """
    try:
        # 验证并转换ObjectId
        try:
            object_id = ObjectId(package_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的套餐ID")

        # 检查套餐是否存在
        existing_package = await mongo_db.db[MongoDBPackageModel.get_collection_name()].find_one({"_id": object_id})
        if not existing_package:
            raise HTTPException(status_code=404, detail="套餐不存在")

        # 准备更新数据（只更新非空字段）
        update_data = package_data.model_dump(exclude_unset=True)
        update_data["update_time"] = datetime.now()

        # 如果是记次套餐且更新了总课程数，但没有设置剩余课程数，则保持原有剩余课程数
        if update_data.get("package_category") == "count_based" and "total_lessons" in update_data:
            if "remaining_lessons" not in update_data:
                update_data["remaining_lessons"] = existing_package.get("remaining_lessons", 0)

        # 执行更新
        result = await mongo_db.db[MongoDBPackageModel.get_collection_name()].update_one(
            {"_id": object_id},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="更新套餐失败")

        # 获取更新后的数据
        updated_package = await mongo_db.db[MongoDBPackageModel.get_collection_name()].find_one({"_id": object_id})
        updated_package["id"] = str(updated_package.pop("_id"))

        return PackageModel(**updated_package)

    except ValueError:
        raise HTTPException(status_code=400, detail="无效的套餐ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新套餐失败: {str(e)}")


@router.delete("/{package_id}", status_code=204)
async def delete_package(package_id: str):
    """
    删除套餐
    """
    try:
        # 验证并转换ObjectId
        try:
            object_id = ObjectId(package_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的套餐ID")

        # 检查套餐是否存在
        existing_package = await mongo_db.db[MongoDBPackageModel.get_collection_name()].find_one({"_id": object_id})
        if not existing_package:
            raise HTTPException(status_code=404, detail="套餐不存在")

        # 删除套餐
        result = await mongo_db.db[MongoDBPackageModel.get_collection_name()].delete_one({"_id": object_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=400, detail="删除套餐失败")

        return

    except ValueError:
        raise HTTPException(status_code=400, detail="无效的套餐ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除套餐失败: {str(e)}")


@router.post("/{package_id}/consume-lesson")
async def consume_lesson(package_id: str):
    """
    消耗课程（仅适用于记次套餐）
    """
    try:
        # 验证并转换ObjectId
        try:
            object_id = ObjectId(package_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的套餐ID")

        # 检查套餐是否存在
        package = await mongo_db.db[MongoDBPackageModel.get_collection_name()].find_one({"_id": object_id})
        if not package:
            raise HTTPException(status_code=404, detail="套餐不存在")

        # 检查是否为记次套餐
        if package.get("package_category") != "count_based":
            raise HTTPException(status_code=400, detail="只有记次套餐可以消耗课程")

        # 检查剩余课程
        remaining_lessons = package.get("remaining_lessons", 0)
        if remaining_lessons <= 0:
            raise HTTPException(status_code=400, detail="课程已用完")

        # 消耗一节课
        result = await mongo_db.db[MongoDBPackageModel.get_collection_name()].update_one(
            {"_id": object_id},
            {
                "$inc": {"remaining_lessons": -1},
                "$set": {"update_time": datetime.now()}
            }
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="消耗课程失败")

        # 获取更新后的套餐
        updated_package = await mongo_db.db[MongoDBPackageModel.get_collection_name()].find_one({"_id": object_id})
        updated_package["id"] = str(updated_package.pop("_id"))

        return {
            "message": "课程消耗成功",
            "remaining_lessons": updated_package.get("remaining_lessons", 0)
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="无效的套餐ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"消耗课程失败: {str(e)}")


@router.get("/{package_id}/status")
async def get_package_status(package_id: str):
    """
    获取套餐状态信息
    """
    try:
        # 验证并转换ObjectId
        try:
            object_id = ObjectId(package_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的套餐ID")

        # 查询套餐
        package = await mongo_db.db[MongoDBPackageModel.get_collection_name()].find_one({"_id": object_id})
        if not package:
            raise HTTPException(status_code=404, detail="套餐不存在")

        package["id"] = str(package.pop("_id"))
        package_model = PackageModel(**package)

        return {
            "is_valid": package_model.is_package_valid,
            "status_text": package_model.package_status_text,
            "is_active": package_model.is_active,
            "package_category": package_model.package_category
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="无效的套餐ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取套餐状态失败: {str(e)}")