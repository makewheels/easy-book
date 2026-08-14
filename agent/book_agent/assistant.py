"""Agent loop — 模型驱动的 tool-use（手写循环，无框架，同 video-2022）。"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from .client import ModelClient
from .schema import ALL_TOOLS
from .tools import BookTools


def build_system_prompt(now: datetime | None = None) -> str:
    """生成系统提示词；注入当前日期，模型才能正确换算“明天/下周一”。"""
    now = now or datetime.now()
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    today = f"{now.strftime('%Y-%m-%d')}（{weekdays[now.weekday()]}）"

    return f"""你是 Easy-Book 泳课学员管理系统的 AI 助手，帮游泳教练管理学员、课包、约课、签到和财务。

今天是 {today}。涉及“今天/明天/下周”等相对日期时，先换算成 YYYY-MM-DD 绝对日期再调工具。

## 核心规则

1. **写操作必须确认**：新增/修改/删除/签到/扣课时等改数据的操作，工具会返回 requiresConfirmation。
   此时你要把计划（做什么、涉及谁、关键数字）清楚告诉用户并等待确认，用户同意后才带确认标记再次执行。
   未确认前不得猜测执行结果。
2. **先查再改**：用户用姓名指代学员时，先 search_students 拿 student_id；
   改套餐先 list_student_packages 拿 package_id；改预约先 get_schedule / list_student_appointments 拿 appointment_id。
   绝不编造 id。
3. **有歧义就追问**：搜索返回多个同名学员时，列出候选让用户选，不要猜。
4. **数据准确**：课时数、金额、时间必须来自工具返回，不要编造；金额保留两位小数。
5. **中文回答**：简洁、口语化，关键数字清晰列出。

## 工具选择指南

- 明天/某天有什么课 → get_schedule(date)
- 这周/一段时间的课 → get_schedule_range
- 学员还有多少课时 → search_students（含 remaining_lessons）或 lessons_overview（全员+低余额预警）
- 学员的课包明细 → list_student_packages
- 利润/营收/分成统计 → profit_stats（可带月份范围）
- 新增学员 → create_student；改资料 → update_student
- 买课包/续费 → create_package（记次给 total_lessons，时长给起止日期）
- 加次数/扣次数 → adjust_package_lessons（delta 正加负扣）
- 设置财务分成 → update_package 改 venue_share（上交俱乐部金额，利润=price-venue_share）
- 约课 → book_appointment（start_time 用 ISO 格式本地时间）
- 取消约课 → cancel_appointment；标记旷课 → set_appointment_status(no_show)
- 签到（扣课时）→ checkin_appointment"""


class BookAssistant:
    """easy-book 助手：LLM + BookTools 的多轮 agent。"""

    MAX_TURNS = 8

    def __init__(
        self,
        tools: BookTools | None = None,
        client: ModelClient | None = None,
    ) -> None:
        self.tools = tools or BookTools()
        self.client = client or ModelClient()

    def answer(self, query: str, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """单轮/多轮问答，返回 {query, answer, trace, messages}。"""
        self.tools.trace.clear()
        messages: list[dict[str, Any]] = [{"role": "system", "content": build_system_prompt()}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": query})

        final_text = ""
        for _ in range(self.MAX_TURNS):
            response = self.client.chat(messages, tools=ALL_TOOLS)

            if not response.tool_calls:
                final_text = response.text
                break

            # 带工具调用的一轮：先记录 assistant 消息
            messages.append({
                "role": "assistant",
                "content": response.text or None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, ensure_ascii=False),
                        },
                    }
                    for tc in response.tool_calls
                ],
            })

            # 逐个执行工具，结果塞回 messages
            for tc in response.tool_calls:
                result = self.tools.execute(tc.name, tc.arguments)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                })
        else:
            final_text = "（已达到最大推理轮数，请简化你的请求）"

        return {
            "query": query,
            "answer": final_text,
            "trace": list(self.tools.trace),
            "messages": messages,
        }
