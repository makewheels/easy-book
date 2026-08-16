"""AI 助手建议问题生成：系统状态驱动候选 + 用户习惯个性化排序（纯 DB 查询，无 LLM）。

候选来源（设计见 docs/agent-memory-and-suggestions.md）：
- low_balance   课时低余额（≤3 节）——教练最高频的日常动作，排最前
- today_checkin 今天有课 → 签到引导
- monthly_profit 本月营收（月初 7 天内权重上浮）
- no_package    新学员还没买课包
- fallback      通用问题（课时总览/明天课表/新增学员）

个性化：agent_queries 集合统计该用户各意图使用次数，score += 8 * min(count, 5)。
"""

from __future__ import annotations

from datetime import datetime, time, timedelta

from api_server.mongo_database import db as mongo_db
from api_server.database import get_database

LOW_BALANCE_THRESHOLD = 3

# 候选意图的基础权重（越大越靠前；个性化加分在其上叠加）
BASE_SCORE = {
    "low_balance": 90,
    "today_checkin": 80,
    "monthly_profit": 60,
    "monthly_profit_early": 85,  # 月初 7 天内
    "no_package": 55,
    "lessons_overview": 50,
    "tomorrow_schedule": 45,
    "new_student": 40,
}


class SuggestionService:

    @staticmethod
    async def build_suggestions(user_id: str = "", limit: int = 3) -> list[dict]:
        candidates = await SuggestionService._state_candidates()
        counts = await SuggestionService._intent_counts(user_id)
        for c in candidates:
            c["score"] = c["base"] + 8 * min(counts.get(c["intent"], 0), 5)
        candidates.sort(key=lambda c: -c["score"])

        seen: set[str] = set()
        result: list[dict] = []
        for c in candidates:
            if c["message"] in seen:
                continue
            seen.add(c["message"])
            result.append({"label": c["label"], "message": c["message"],
                           "intent": c["intent"], "score": c["score"]})
            if len(result) >= limit:
                break
        return result

    # ── 状态候选 ────────────────────────────────────────────

    @staticmethod
    async def _state_candidates() -> list[dict]:
        out: list[dict] = []

        # 低余额：剩余最少的那位学员（多人时消息里带总数）
        students = await mongo_db.get_students()
        low: list[tuple[str, int]] = []
        no_pkg: list[str] = []
        for stu in students:
            packages = await mongo_db.get_student_packages(stu["id"])
            remaining = sum((p.get("count_based_info") or {}).get("remaining_lessons", 0)
                            for p in packages)
            total = sum((p.get("count_based_info") or {}).get("total_lessons", 0)
                        for p in packages)
            if not packages:
                no_pkg.append(stu.get("name", ""))
            elif 0 < remaining <= LOW_BALANCE_THRESHOLD:
                low.append((stu.get("name", ""), remaining))
        if low:
            low.sort(key=lambda x: x[1])
            name, rem = low[0]
            msg = (f"{name}只剩{rem}节课了，还有其他{len(low)-1}位学员课时不多，看看续课建议"
                   if len(low) > 1 else f"{name}只剩{rem}节课了，看看续课建议")
            out.append({"intent": "low_balance", "label": "续课提醒",
                        "message": msg, "base": BASE_SCORE["low_balance"]})

        # 今天有课 → 签到引导
        now = datetime.now()
        day_start = datetime.combine(now.date(), time.min)
        day_end = day_start + timedelta(days=1)
        db = get_database().db
        today_count = await db.appointments.count_documents({
            "start_time": {"$gte": day_start, "$lt": day_end},
            "status": {"$in": ["scheduled", "checked", "completed"]},
        })
        if today_count > 0:
            out.append({"intent": "today_checkin", "label": "今日课程",
                        "message": "今天有什么课？上完的帮我签到",
                        "base": BASE_SCORE["today_checkin"]})

        # 营收（月初 7 天上浮）
        early = now.day <= 7
        out.append({"intent": "monthly_profit", "label": "本月营收",
                    "message": "这个月收入多少？",
                    "base": BASE_SCORE["monthly_profit_early" if early else "monthly_profit"]})

        # 新学员还没买课包
        if no_pkg:
            out.append({"intent": "no_package", "label": "购买课包",
                        "message": f"{no_pkg[0]}还没有课包，帮ta买一个",
                        "base": BASE_SCORE["no_package"]})

        # 兜底通用候选
        out.append({"intent": "lessons_overview", "label": "课时总览",
                    "message": "现在有哪些学员？各自的课时余额怎么样？",
                    "base": BASE_SCORE["lessons_overview"]})
        out.append({"intent": "tomorrow_schedule", "label": "明天课表",
                    "message": "明天有什么课？",
                    "base": BASE_SCORE["tomorrow_schedule"]})
        out.append({"intent": "new_student", "label": "新增学员",
                    "message": "帮我新增一个学员",
                    "base": BASE_SCORE["new_student"]})
        return out

    # ── 用户习惯 ────────────────────────────────────────────

    @staticmethod
    async def _intent_counts(user_id: str) -> dict[str, int]:
        if not user_id:
            return {}
        db = get_database().db
        counts: dict[str, int] = {}
        async for doc in db.agent_queries.find({"user_id": user_id}):
            intent = doc.get("intent") or "general"
            counts[intent] = counts.get(intent, 0) + 1
        return counts
