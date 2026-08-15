"""日程/预约域工具 schema：课表查询 + 约课/取消/签到/状态写操作。"""

from __future__ import annotations

from typing import Any

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_schedule",
            "description": (
                "查询某一天的课程表（回答“明天有什么课/今天谁上课”用这个）。"
                "返回按时间排序的时段数组：time、course_id、course_title、students"
                "（每个学员含 name、appointment_id、student_id、status、remaining_lessons）。"
                "date 格式 YYYY-MM-DD，相对日期（明天/后天/下周一）请先换算成绝对日期。"
                "示例：{\"date\": \"2026-08-19\"}。"
                "做不到：只查单天，多天范围用 get_schedule_range。"
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
                "示例：{\"start_date\": \"2026-08-17\", \"end_date\": \"2026-08-23\"}。"
                "做不到：范围超过 90 天会被拒绝，需分段查。"
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
                "做不到：只按单个学员查；看某天全员课程用 get_schedule。"
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
                "示例：{\"student_id\": \"6a7f…\", \"start_time\": \"2026-08-19T21:00:00\"}。"
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
                "做不到：不扣也不退课时；记录出勤用 checkin_appointment，标记旷课用 set_appointment_status。"
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
                "示例：{\"appointment_id\": \"6a7f…\", \"student_id\": \"6a7f…\"}。"
                "做不到：只扣 1 课时，不能一次扣多节；学员套餐余量为 0 时会失败。"
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
                "做不到：只改状态不动课时——签到扣课时用 checkin_appointment。"
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

# 本域写操作名单（执行前需要确认）
WRITE_TOOLS: set[str] = {
    "book_appointment",
    "cancel_appointment",
    "checkin_appointment",
    "set_appointment_status",
}
