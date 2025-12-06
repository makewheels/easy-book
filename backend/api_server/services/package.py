"""
套餐服务模块
处理套餐类型相关的业务逻辑，包括记次套餐和时长套餐的管理
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dateutil.relativedelta import relativedelta


class PackageService:
    """套餐服务类"""

    # 套餐类别定义
    PACKAGE_CATEGORIES = {
        "count_based": "记次套餐",
        "time_based": "时长套餐"
    }

    # 时长套餐类型定义
    DURATION_TYPES = {
        "monthly": "月卡",
        "quarterly": "季卡",
        "yearly": "年卡",
        "custom": "自定义"
    }

    @staticmethod
    def calculate_package_end_date(duration_type: str, start_date: datetime = None,
                                 custom_days: int = None) -> Optional[datetime]:
        """
        计算套餐到期时间

        Args:
            duration_type: 时长类型 (monthly, quarterly, yearly, custom)
            start_date: 开始时间，默认为当前时间
            custom_days: 自定义天数(仅custom类型使用)

        Returns:
            到期时间，如果没有设置则返回None
        """
        if not start_date:
            start_date = datetime.now()

        if duration_type == "monthly":
            return start_date + relativedelta(months=1)
        elif duration_type == "quarterly":
            return start_date + relativedelta(months=3)
        elif duration_type == "yearly":
            return start_date + relativedelta(years=1)
        elif duration_type == "custom" and custom_days:
            return start_date + timedelta(days=custom_days)

        return None

    @staticmethod
    def get_package_status_text(package_data: Dict[str, Any]) -> str:
        """
        获取套餐状态文本

        Args:
            package_data: 包含套餐信息的字典

        Returns:
            套餐状态文本
        """
        package_category = package_data.get("package_category", "count_based")

        if package_category == "count_based":
            # 记次套餐
            remaining = package_data.get("remaining_lessons", 0)
            total = package_data.get("total_lessons", 0)
            return f"{remaining}/{total}次"
        else:
            # 时长套餐
            if package_data.get("unlimited_access", False):
                return "永久有效"

            package_end_date = package_data.get("package_end_date")
            if not package_end_date:
                return "永久有效"

            # 处理字符串格式的日期
            if isinstance(package_end_date, str):
                try:
                    package_end_date = datetime.fromisoformat(package_end_date.replace('Z', '+00:00'))
                except:
                    return "无效日期"

            days_left = (package_end_date - datetime.now()).days
            if days_left <= 0:
                return "已过期"
            elif days_left <= 30:
                return f"{days_left}天后过期"
            else:
                return package_end_date.strftime("%Y/%m/%d到期")

    @staticmethod
    def is_package_valid(package_data: Dict[str, Any]) -> bool:
        """
        检查套餐是否有效

        Args:
            package_data: 包含套餐信息的字典

        Returns:
            套餐是否有效
        """
        package_category = package_data.get("package_category", "count_based")

        if package_category == "count_based":
            # 记次套餐：检查剩余课程
            remaining = package_data.get("remaining_lessons", 0)
            return remaining > 0
        else:
            # 时长套餐：检查到期时间
            if package_data.get("unlimited_access", False):
                return True

            package_end_date = package_data.get("package_end_date")
            if not package_end_date:
                return True

            # 处理字符串格式的日期
            if isinstance(package_end_date, str):
                try:
                    package_end_date = datetime.fromisoformat(package_end_date.replace('Z', '+00:00'))
                except:
                    return False

            return datetime.now() <= package_end_date

    @staticmethod
    def process_package_data_for_creation(create_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理创建学生时的套餐数据

        Args:
            create_data: 创建学生的原始数据

        Returns:
            处理后的套餐数据
        """
        package_category = create_data.get("package_category", "count_based")

        # 设置兼容字段
        processed_data = create_data.copy()
        processed_data["package_type"] = create_data.get("original_package_type", "1v1")

        if package_category == "count_based":
            # 记次套餐：设置初始剩余课程数
            total_lessons = create_data.get("total_lessons", 0)
            processed_data["remaining_lessons"] = total_lessons
            # 清空时长套餐相关字段
            processed_data["package_end_date"] = None
            processed_data["package_duration_type"] = None
            processed_data["package_duration_days"] = None
            processed_data["unlimited_access"] = False
        else:
            # 时长套餐：计算到期时间
            duration_type = create_data.get("package_duration_type")
            custom_days = create_data.get("package_duration_days")
            unlimited = create_data.get("unlimited_access", False)

            if not unlimited and duration_type:
                end_date = PackageService.calculate_package_end_date(
                    duration_type, custom_days=custom_days
                )
                processed_data["package_end_date"] = end_date
            else:
                processed_data["package_end_date"] = None

            # 清空记次套餐相关字段
            processed_data["total_lessons"] = None
            processed_data["remaining_lessons"] = None

        return processed_data

    @staticmethod
    def get_package_info_display(package_data: Dict[str, Any]) -> Dict[str, str]:
        """
        获取套餐显示信息

        Args:
            package_data: 包含套餐信息的字典

        Returns:
            包含显示信息的字典
        """
        package_category = package_data.get("package_category", "count_based")
        original_package_type = package_data.get("original_package_type", "1v1")

        result = {
            "category": PackageService.PACKAGE_CATEGORIES.get(package_category, package_category),
            "type": original_package_type,
            "status": PackageService.get_package_status_text(package_data),
            "valid": "有效" if PackageService.is_package_valid(package_data) else "无效"
        }

        if package_category == "time_based":
            duration_type = package_data.get("package_duration_type")
            if duration_type:
                result["duration"] = PackageService.DURATION_TYPES.get(duration_type, duration_type)

            if package_data.get("unlimited_access", False):
                result["duration"] = "永久"

        return result