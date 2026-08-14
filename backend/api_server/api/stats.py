"""
统计API
财务分成与利润统计：教练利润 = 套餐售价(price) - 上交俱乐部(venue_share)
"""

from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api_server.mongo_database import db as mongo_db
from api_server.models import MongoDBPackageModel

router = APIRouter(tags=["stats"])


def _parse_date(value: str, field: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail=f"{field} 格式无效，请使用 YYYY-MM-DD")


@router.get("/profit")
async def profit_stats(
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD（默认全部）"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD（默认今天）"),
):
    """
    利润统计：按套餐创建时间口径统计售价、上交俱乐部、教练利润，并按月分组
    """
    try:
        query = {}
        start_dt = _parse_date(start_date, "start_date") if start_date else None
        if end_date:
            # 结束日期包含当天
            end_dt = _parse_date(end_date, "end_date")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        else:
            end_dt = None

        if start_dt or end_dt:
            query["create_time"] = {}
            if start_dt:
                query["create_time"]["$gte"] = start_dt
            if end_dt:
                query["create_time"]["$lte"] = end_dt

        total_revenue = 0.0
        total_venue_share = 0.0
        package_count = 0
        by_month = {}
        packages = []

        async for pkg in mongo_db.db[MongoDBPackageModel.get_collection_name()].find(query).sort("create_time", 1):
            price = float(pkg.get("price") or 0)
            venue_share = float(pkg.get("venue_share") or 0)
            profit = round(price - venue_share, 2)

            total_revenue += price
            total_venue_share += venue_share
            package_count += 1

            create_time = pkg.get("create_time")
            if isinstance(create_time, datetime):
                month_key = create_time.strftime("%Y-%m")
                month = by_month.setdefault(month_key, {
                    "month": month_key,
                    "package_count": 0,
                    "revenue": 0.0,
                    "venue_share": 0.0,
                    "profit": 0.0,
                })
                month["package_count"] += 1
                month["revenue"] = round(month["revenue"] + price, 2)
                month["venue_share"] = round(month["venue_share"] + venue_share, 2)
                month["profit"] = round(month["profit"] + profit, 2)

            packages.append({
                "package_id": str(pkg.get("_id")),
                "student_id": pkg.get("student_id"),
                "name": pkg.get("name"),
                "package_type": pkg.get("package_type"),
                "price": price,
                "venue_share": venue_share,
                "profit": profit,
                "create_time": create_time.isoformat() if isinstance(create_time, datetime) else create_time,
            })

        # 附带学员姓名
        student_ids = list({p["student_id"] for p in packages if p.get("student_id")})
        name_map = {}
        for sid in student_ids:
            student = await mongo_db.get_student(sid)
            if student:
                name_map[sid] = student.get("name", "")
        for p in packages:
            p["student_name"] = name_map.get(p.get("student_id"), "")

        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "package_count": package_count,
                "total_revenue": round(total_revenue, 2),
                "total_venue_share": round(total_venue_share, 2),
                "total_profit": round(total_revenue - total_venue_share, 2),
                "by_month": sorted(by_month.values(), key=lambda m: m["month"], reverse=True),
                "packages": packages,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取利润统计失败: {str(e)}")


@router.get("/lessons")
async def lessons_stats():
    """
    课时概览：每个学员的剩余课时汇总（便于发现快用完的学员）
    """
    try:
        students = await mongo_db.get_students()
        result = []
        total_remaining = 0
        for student in students:
            packages = await mongo_db.get_student_packages(student["id"])
            remaining = sum(
                (p.get("count_based_info") or {}).get("remaining_lessons", 0)
                for p in packages
            )
            total = sum(
                (p.get("count_based_info") or {}).get("total_lessons", 0)
                for p in packages
            )
            if total == 0 and remaining == 0 and not packages:
                continue
            total_remaining += remaining
            result.append({
                "student_id": student["id"],
                "student_name": student.get("name", ""),
                "package_count": len(packages),
                "total_lessons": total,
                "remaining_lessons": remaining,
                "low_balance": 0 < remaining <= 3,
            })

        result.sort(key=lambda x: x["remaining_lessons"])

        return {
            "code": 200,
            "message": "获取成功",
            "data": {
                "student_count": len(result),
                "total_remaining_lessons": total_remaining,
                "low_balance_students": [r for r in result if r["low_balance"]],
                "students": result,
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取课时统计失败: {str(e)}")
