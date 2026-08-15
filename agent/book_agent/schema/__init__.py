"""Easy-Book agent 工具 schema（OpenAI function-calling 格式）。

按业务域拆分（students / appointments / packages），本包聚合导出：
- ALL_TOOLS：全部工具 schema（传给模型）
- WRITE_TOOLS：写操作名单（执行前需两步确认）

约定（与 video-2022 一致）：
- 参数为裸 JSON Schema；description 是写给模型的操作手册（何时用 + 示例 + 做不到什么）
- 工具名 == BookTools 里的方法名（getattr 分发，无注册器）
- 写操作的 description 带 ⚠️ 标记

按域拆分也是将来"渐进式工具加载"（按任务只注入相关域）的前提。
"""

from __future__ import annotations

from typing import Any

from . import appointments, packages, students

ALL_TOOLS: list[dict[str, Any]] = students.TOOLS + appointments.TOOLS + packages.TOOLS

# 写操作工具名单（执行前需要确认）= 各域声明的并集
WRITE_TOOLS: set[str] = students.WRITE_TOOLS | appointments.WRITE_TOOLS | packages.WRITE_TOOLS

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
