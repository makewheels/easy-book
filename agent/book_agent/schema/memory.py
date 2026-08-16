"""用户记忆域：让 agent 把教练的习惯/事实主动存入长期记忆。"""

from __future__ import annotations

from typing import Any

SAVE_USER_MEMORY_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "save_user_memory",
        "description": (
            "⚠️ 写操作（需确认）：把教练说过的、以后还有用的信息记入长期记忆。五种类型：\n"
            "- preference 偏好习惯：如'新课包默认1对1/12节/1600元'、'回答简洁点'\n"
            "- fact 业务事实：如'俱乐部分成一般600'、'冬天改下午3点开课'\n"
            "- person 学员相关：如'小红是张钰桐的小名'、'李家姐妹一起上课'\n"
            "- process 未完成事项：如'曹赫的分成调整还没办'\n"
            "- pattern 时间规律：如'教练月初会查营收'\n"
            "只在教练明确表达或强烈暗示时记录；一次性的事（某次约课时间、某个临时问题）不要记。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "kind": {
                    "type": "string",
                    "enum": ["preference", "fact", "person", "process", "pattern"],
                    "description": "记忆类型",
                },
                "content": {
                    "type": "string",
                    "description": "一句话描述这条记忆，包含具体的人/数值/规则",
                },
            },
            "required": ["kind", "content"],
        },
    },
}

TOOLS: list[dict[str, Any]] = [SAVE_USER_MEMORY_TOOL]

# 写记忆也走两步确认：让教练看到"我将记住什么"
WRITE_TOOLS: set[str] = {"save_user_memory"}
