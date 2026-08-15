"""学员域工具 schema：查询（search_students/get_student）+ 写操作（增/改/删）。"""

from __future__ import annotations

from typing import Any

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_students",
            "description": (
                "查询学员列表，可按姓名/电话模糊搜索。返回学员数组，含 id、name、phone、"
                "remaining_lessons(剩余课时)、total_lessons(总课时)。"
                "用户问“有几个学员/学员名单”时也用它（省略 search 返回全部）。"
                "用户提到学员名字时，先用本工具拿到 student_id，再调其他工具；不要编造 id。"
                "示例：{\"search\": \"张\"}。"
                "做不到：不能按课时余量/课包/创建时间过滤；最多返回 limit 条，超过时结果不完整。"
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
            "description": (
                "查询单个学员详情（含套餐聚合的剩余/总课时）。需要 student_id。"
                "做不到：不能按姓名查——只知道姓名时先用 search_students 拿 id。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "student_id": {"type": "string", "description": "学员ID（先用 search_students 获得）"},
                },
                "required": ["student_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_student",
            "description": (
                "新增学员。⚠️ 写操作需确认。姓名必填，其余可选。"
                "示例：{\"name\": \"张小游\", \"phone\": \"13800138000\"}。"
                "做不到：不查重名，同名学员会并存——建前可先 search_students 确认。"
            ),
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
            "description": (
                "修改学员资料（只传要改的字段）。⚠️ 写操作需确认。"
                "示例：{\"student_id\": \"6a7f25ea…\", \"phone\": \"13900139000\"}。"
                "做不到：不能批量改多个学员，一次一个。"
            ),
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
]

# 本域写操作名单（执行前需要确认）
WRITE_TOOLS: set[str] = {"create_student", "update_student", "delete_student"}
