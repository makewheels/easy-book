"""套餐/财务域工具 schema：课包查询/财务统计 + 课包写操作。"""

from __future__ import annotations

from typing import Any

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_student_packages",
            "description": (
                "查询某学员的所有套餐（课包）。返回套餐数组：id、name、package_type"
                "（1v1/1v2/... 或 time_based）、price 售价、venue_share 上交俱乐部、"
                "count_based_info {total_lessons, remaining_lessons}。"
                "要“加次数/扣次数”时先用本工具找到 package_id。"
                "做不到：只按单个学员查，不能查全体学员的课包。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "学员ID"},
                },
                "required": ["student_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_package",
            "description": (
                "查询单个套餐详情（价格、分成、剩余课时、有效性）。需要 package_id。"
                "做不到：不能按学员姓名查——先用 list_student_packages 拿 package_id。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "package_id": {"type": "string", "description": "套餐ID"},
                },
                "required": ["package_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "profit_stats",
            "description": (
                "统计利润（回答“这个月赚了多少/利润统计”）。"
                "口径：按套餐创建时间。教练利润 = 售价 price - 上交俱乐部 venue_share。"
                "返回 total_revenue 总营收、total_venue_share 总上交、total_profit 总利润、"
                "by_month 按月明细、packages 逐单明细（含学员姓名）。"
                "start_date/end_date 可选，格式 YYYY-MM-DD，省略则统计全部。"
                "示例：{\"start_date\": \"2026-08-01\", \"end_date\": \"2026-08-31\"}。"
                "做不到：口径只有套餐创建时间，不支持消课口径（“上课赚了多少”无法统计）。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD（可选）"},
                    "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD（可选）"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lessons_overview",
            "description": (
                "全体学员课时概览：每人剩余课时、低余额预警（≤3 节）。"
                "回答“谁快没课时了/还剩多少节课”用这个。"
                "做不到：只返回全员概览，不能过滤单个学员；不含财务数据（财务用 profit_stats）。"
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_package",
            "description": (
                "为学员新增套餐（买课包/续费）。⚠️ 写操作需确认。"
                "记次套餐（1v1/1v2/1v3/1v5/count_based）传 total_lessons；"
                "时长套餐（package_type=time_based）传 start_date/end_date。"
                "price=售价(元)，venue_share=上交俱乐部(元)，教练利润=price-venue_share。"
                "记次示例：{\"student_id\": \"6a7f…\", \"name\": \"自由泳1对1\", \"package_type\": \"1v1\", "
                "\"price\": 1600, \"venue_share\": 600, \"total_lessons\": 12}；"
                "时长套餐把 total_lessons 换成 start_date/end_date。"
                "做不到：记次不传 total_lessons、时长不传起止日期都会失败。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "学员ID"},
                    "name": {"type": "string", "description": "套餐名称，如“1对1暑期包”"},
                    "package_type": {
                        "type": "string",
                        "description": "套餐类型：1v1/1v2/1v3/1v5（记次）或 time_based（时长）",
                    },
                    "price": {"type": "number", "description": "售价(元)，必须大于 0"},
                    "venue_share": {"type": "number", "description": "上交俱乐部(元)，≥0"},
                    "total_lessons": {"type": "integer", "description": "记次套餐总课时（记次必填）"},
                    "start_date": {"type": "string", "description": "时长套餐开始日期 YYYY-MM-DD（时长套餐用）"},
                    "end_date": {"type": "string", "description": "时长套餐结束日期 YYYY-MM-DD（时长套餐用）"},
                },
                "required": ["student_id", "name", "package_type", "price", "venue_share"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_package",
            "description": (
                "修改套餐（只传要改的字段）。⚠️ 写操作需确认。"
                "“设置/调整财务分成”就是改 venue_share（上交俱乐部金额）。"
                "示例：{\"package_id\": \"6a7f…\", \"venue_share\": 800}。"
                "做不到：不改课时数——加/扣次数用 adjust_package_lessons。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "package_id": {"type": "string", "description": "套餐ID"},
                    "name": {"type": "string", "description": "套餐名称"},
                    "package_type": {"type": "string", "description": "套餐类型"},
                    "price": {"type": "number", "description": "售价(元)"},
                    "venue_share": {"type": "number", "description": "上交俱乐部(元)，即财务分成"},
                },
                "required": ["package_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "adjust_package_lessons",
            "description": (
                "给套餐加次数/扣次数（“给某某加 5 节课”用这个）。⚠️ 写操作需确认。"
                "流程：search_students 找到学员 → list_student_packages 找到 package_id → 本工具。"
                "delta 正数为加、负数为扣；adjust_total=true 时总课时同步变化（续费场景）。"
                "示例：{\"package_id\": \"6a7f…\", \"delta\": 5, \"reason\": \"续费赠送\"}。"
                "做不到：delta 为 0 无意义；一次只能调一个套餐，跨套餐需分别调。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "package_id": {"type": "string", "description": "套餐ID"},
                    "delta": {"type": "integer", "description": "课时变化量，正数加、负数扣"},
                    "adjust_total": {"type": "boolean", "description": "是否同步调整总课时，默认 false", "default": False},
                    "reason": {"type": "string", "description": "调整原因，如“续费赠送”"},
                },
                "required": ["package_id", "delta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_package",
            "description": "删除套餐。⚠️ 危险写操作需确认，不可恢复。",
            "parameters": {
                "type": "object",
                "properties": {
                    "package_id": {"type": "string", "description": "套餐ID"},
                },
                "required": ["package_id"],
            },
        },
    },
]

# 本域写操作名单（执行前需要确认）
WRITE_TOOLS: set[str] = {
    "create_package",
    "update_package",
    "adjust_package_lessons",
    "delete_package",
}
