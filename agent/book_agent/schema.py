"""Easy-Book agent 工具 schema（OpenAI function-calling 格式）。

约定（与 video-2022 一致）：
- 参数为裸 JSON Schema；description 是写给模型的操作手册
- 工具名 == BookTools 里的方法名（getattr 分发，无注册器）
- 写操作的 description 带 ⚠️ 标记
"""

from __future__ import annotations

from typing import Any

ALL_TOOLS: list[dict[str, Any]] = [
    # ────────────────────────── 查询：学员 ──────────────────────────
    {
        "type": "function",
        "function": {
            "name": "search_students",
            "description": (
                "查询学员列表，可按姓名/电话模糊搜索。返回学员数组，含 id、name、phone、"
                "remaining_lessons(剩余课时)、total_lessons(总课时)。"
                "用户问“有几个学员/学员名单”时也用它（省略 search 返回全部）。"
                "用户提到学员名字时，先用本工具拿到 student_id，再调其他工具；不要编造 id。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "search": {"type": "string", "description": "姓名或电话关键词，省略则返回全部学员"},
                    "limit": {"type": "integer", "description": "最多返回条数，默认 50", "default": 50},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_student",
            "description": "查询单个学员详情（含套餐聚合的剩余/总课时）。需要 student_id。",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "学员ID（先用 search_students 获得）"},
                },
                "required": ["student_id"],
            },
        },
    },
    # ────────────────────────── 查询：日程/预约 ──────────────────────────
    {
        "type": "function",
        "function": {
            "name": "get_schedule",
            "description": (
                "查询某一天的课程表（回答“明天有什么课/今天谁上课”用这个）。"
                "返回按时间排序的时段数组：time、course_id、course_title、students"
                "（每个学员含 name、appointment_id、student_id、status、remaining_lessons）。"
                "date 格式 YYYY-MM-DD，相对日期（明天/后天/下周一）请先换算成绝对日期。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "日期，格式 YYYY-MM-DD"},
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_schedule_range",
            "description": (
                "批量查询一个日期范围内每天的课程表（回答“这周的课”用这个，最多 90 天）。"
                "返回 {日期: {weekday, slots}} 字典。日期格式 YYYY-MM-DD。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "开始日期 YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "结束日期 YYYY-MM-DD"},
                },
                "required": ["start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_student_appointments",
            "description": (
                "查询某学员的预约记录（含课程时间、状态）。"
                "status 取值：scheduled 待上课 / completed|checked 已签到 / cancelled|cancel 已取消。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "学员ID"},
                    "status": {"type": "string", "description": "可选，按状态过滤"},
                },
                "required": ["student_id"],
            },
        },
    },
    # ────────────────────────── 查询：套餐/财务 ──────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_student_packages",
            "description": (
                "查询某学员的所有套餐（课包）。返回套餐数组：id、name、package_type"
                "（1v1/1v2/... 或 time_based）、price 售价、venue_share 上交俱乐部、"
                "count_based_info {total_lessons, remaining_lessons}。"
                "要“加次数/扣次数”时先用本工具找到 package_id。"
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
            "description": "查询单个套餐详情（价格、分成、剩余课时、有效性）。需要 package_id。",
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
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    # ────────────────────────── 写操作：学员 ──────────────────────────
    {
        "type": "function",
        "function": {
            "name": "create_student",
            "description": "新增学员。⚠️ 写操作需确认。姓名必填，其余可选。",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "学员姓名"},
                    "gender": {"type": "string", "description": "性别（男/女）", "enum": ["男", "女"]},
                    "age": {"type": "integer", "description": "年龄"},
                    "phone": {"type": "string", "description": "联系电话"},
                    "emergency_contact": {"type": "string", "description": "紧急联系人"},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_student",
            "description": "修改学员资料（只传要改的字段）。⚠️ 写操作需确认。",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "学员ID"},
                    "name": {"type": "string", "description": "姓名"},
                    "gender": {"type": "string", "description": "性别", "enum": ["男", "女"]},
                    "age": {"type": "integer", "description": "年龄"},
                    "phone": {"type": "string", "description": "联系电话"},
                    "emergency_contact": {"type": "string", "description": "紧急联系人"},
                },
                "required": ["student_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_student",
            "description": (
                "删除学员。⚠️ 危险写操作需确认：会级联删除该学员的套餐、预约、考勤记录，不可恢复。"
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
    # ────────────────────────── 写操作：套餐 ──────────────────────────
    {
        "type": "function",
        "function": {
            "name": "create_package",
            "description": (
                "为学员新增套餐（买课包/续费）。⚠️ 写操作需确认。"
                "记次套餐（1v1/1v2/1v3/1v5/count_based）传 total_lessons；"
                "时长套餐（package_type=time_based）传 start_date/end_date。"
                "price=售价(元)，venue_share=上交俱乐部(元)，教练利润=price-venue_share。"
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
    # ────────────────────────── 写操作：预约/考勤 ──────────────────────────
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": (
                "给学员预约上课。⚠️ 写操作需确认。"
                "start_time 为 ISO 格式本地时间（如 2026-08-15T10:00:00），相对说法先换算。"
                "返回带 weekday（所约日期的星期几）：向用户展示计划时务必核对它与用户说的星期是否一致，"
                "不一致说明日期换算错了，重算后再约。"
                "同一时段已有课程时自动并入该课程（多人班）；学员该时段已有预约会被拒绝。"
                "可先 get_schedule 查看当天已有安排。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "学员ID"},
                    "start_time": {"type": "string", "description": "开始时间，ISO 格式 YYYY-MM-DDTHH:MM:SS"},
                    "duration_minutes": {"type": "integer", "description": "时长（分钟），默认 60", "default": 60},
                },
                "required": ["student_id", "start_time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": (
                "取消学员的某次预约（删除预约记录，不扣课时）。⚠️ 写操作需确认。"
                "appointment_id 可从 get_schedule / list_student_appointments 获得。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "string", "description": "预约ID"},
                },
                "required": ["appointment_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "checkin_appointment",
            "description": (
                "学员签到：从其余量的套餐扣 1 课时并记录考勤。⚠️ 写操作需确认（会扣课时）。"
                "需要 appointment_id 和 student_id（get_schedule 的 slots.students 里都有）。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "string", "description": "预约ID"},
                    "student_id": {"type": "string", "description": "学员ID"},
                },
                "required": ["appointment_id", "student_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_appointment_status",
            "description": (
                "设置预约状态（如标记旷课 no_show、恢复为 scheduled）。⚠️ 写操作需确认。"
                "status 取值：scheduled / completed / cancelled / no_show。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "string", "description": "预约ID"},
                    "status": {
                        "type": "string",
                        "enum": ["scheduled", "completed", "cancelled", "no_show"],
                        "description": "目标状态",
                    },
                },
                "required": ["appointment_id", "status"],
            },
        },
    },
]

# 写操作工具名单（执行前需要确认）
WRITE_TOOLS: set[str] = {
    "create_student",
    "update_student",
    "delete_student",
    "create_package",
    "update_package",
    "adjust_package_lessons",
    "delete_package",
    "book_appointment",
    "cancel_appointment",
    "checkin_appointment",
    "set_appointment_status",
}

# 两步确认协议：写操作统一追加 confirm 参数。
# 首次调用不带 confirm（或 false）只返回执行计划（requiresConfirmation）；
# 用户明确同意后，模型带 confirm=true 重调同一工具才真正执行。
_CONFIRM_PARAM = {
    "type": "boolean",
    "description": (
        "确认标记。首次调用请省略——工具只会返回执行计划供用户确认，不改数据；"
        "用户明确同意后，带 confirm=true 重新调用本工具才真正执行。"
    ),
    "default": False,
}
for _tool in ALL_TOOLS:
    if _tool["function"]["name"] in WRITE_TOOLS:
        _tool["function"]["parameters"]["properties"]["confirm"] = _CONFIRM_PARAM
