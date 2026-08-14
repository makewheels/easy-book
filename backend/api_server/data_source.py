"""用户来源标记：区分真实用户与 AI 测试用户（模式与 speakup 的 data_source 一致）。

资源（学员/课包/预约/签到）都属于登录的教练，因此来源标记只落在用户这一层：
教练是 ai_test，其名下数据即测试数据，供后续评测识别与抽取。
"""

from typing import Literal

SourceType = Literal["human", "ai_test"]
DEFAULT_SOURCE_TYPE: SourceType = "human"


def normalize_source_type(value: object) -> SourceType:
    """历史缺字段或未知值都按真实用户处理，避免误把生产数据判成测试数据。"""
    return "ai_test" if value == "ai_test" else DEFAULT_SOURCE_TYPE
