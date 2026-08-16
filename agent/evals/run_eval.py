"""easy-book 评测 runner：脚本化模拟用户驱动 agent，规则断言判定（后端状态+轨迹+回答）。

用法（在 agent/ 目录）：
  EASY_BOOK_API_URL=http://localhost:8002 uv run python evals/run_eval.py            # 单轮
  EASY_BOOK_API_URL=http://localhost:8002 uv run python evals/run_eval.py --passes 3 # Pass^k

设计参照《深入理解 AI Agent》第7章：
- 双重覆盖：轨迹断言（工具序列）+ 状态断言（后端真实数据），防"说了没做到/做到了但违规"
- 模拟用户：固定脚本 + 渐进式信息透露（when_asked 追问应答），可复现、零额外 LLM 成本
- 一票否决：写操作未经 requiresConfirmation 计划直接执行 → veto
- Pass^k：--passes 多轮重跑，轮间重新播种（seed --wipe），全部通过才算 Pass^k 通过
- 失败归因：记录每个失败任务的首个失败断言与首个工具错误
- read-back 观测：写操作执行后是否回查、写返回值是否已含写后状态

期望值全部运行时从 seed_report.json / ledger_parsed.json 计算，不硬编码。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENT_ROOT = HERE.parent
sys.path.insert(0, str(AGENT_ROOT))

import os
os.environ.setdefault("EASY_BOOK_API_URL", "http://localhost:8002")

import requests  # noqa: E402

from book_agent.assistant import BookAssistant, LLMError  # noqa: E402
from book_agent.schema import WRITE_TOOLS  # noqa: E402
from book_agent.tools import BookTools  # noqa: E402

API = os.environ["EASY_BOOK_API_URL"]
TASKS = json.loads((HERE / "tasks.json").read_text(encoding="utf-8"))["tasks"]
SEED_REPORT = HERE / "reports" / "seed_report.json"
PARSED = HERE / "seed" / "data" / "ledger_parsed.json"
REPORT_DIR = HERE / "reports"

MAX_CONFIRM_ROUNDS = 4
# 模型在文本中请求确认的常见措辞（未调工具先出计划，同样需要模拟用户表态）
CONFIRM_ASK_PATTERNS = [
    "是否现在执行", "是否执行", "确认无误后", "请确认", "确认执行吗",
    "要执行吗", "回复“确认”", "回复\"确认\"", "确定要", "是否要继续",
    "确认后执行", "需您确认", "需要您的确认", "等待您的确认",
]
# 模型在追问/征求补充信息的常见措辞（不只看问号——模型可能用陈述句提问）
ASK_MARKERS = ["？", "?", "请提供", "请告诉我", "请补充", "您是否", "需要确认", "是否"]
READ_TOOLS = {
    "search_students", "get_student", "get_schedule", "get_schedule_range",
    "list_student_appointments", "list_student_packages", "get_package",
    "profit_stats", "lessons_overview",
}


# ── 期望值（运行时计算，不硬编码）───────────────────────────
def compute_expectations() -> dict:
    seed = json.loads(SEED_REPORT.read_text(encoding="utf-8"))
    parsed = json.loads(PARSED.read_text(encoding="utf-8"))
    by_name = {s["name"]: s for s in seed["students"]}
    first_date = {s["name"]: next((a["date"] for a in p["attendance"]), None)
                  for p in parsed["students"] for s in [by_name.get(p["name"])] if s}

    today = date.today()
    window_start = today - timedelta(days=90)

    low_balance, revenue_3m, new_students = [], 0.0, 0
    for name, item in by_name.items():
        remaining = item["total"] - item["attendance_ok"] if item["total"] else None
        if remaining is not None and remaining <= 3:
            low_balance.append(name)
        fd = first_date.get(name)
        if fd and date.fromisoformat(fd) >= window_start:
            new_students += 1
            revenue_3m += item.get("imported_price") or 0

    ldm = by_name.get("李冬梅")
    schedule_day = [p["name"] for p in parsed["students"]
                    if any(a["date"] == "2026-06-02" for a in p["attendance"])]

    return {
        "tomorrow": (today + timedelta(days=1)).isoformat(),
        "low_balance_names": low_balance,
        "revenue_3m": round(revenue_3m, 2),
        "new_students_3m": new_students,
        "li_dongmei_remaining": (ldm["total"] - ldm["attendance_ok"]) if ldm else None,
        "schedule_2026_06_02": schedule_day,
    }


# ── HTTP 状态检查 ─────────────────────────────────────────
def _unwrap(resp: requests.Response):
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "code" in data and "data" in data:
        return data.get("data")
    return data


def find_student(name: str) -> dict | None:
    rows = _unwrap(requests.get(f"{API}/api/students/", params={"search": name}, timeout=10))
    for r in rows or []:
        if r.get("name") == name:
            return r
    return None


def get_package_of(name: str) -> dict | None:
    stu = find_student(name)
    if not stu:
        return None
    pkgs = _unwrap(requests.get(f"{API}/api/packages/student/{stu['id']}", timeout=10))
    return (pkgs or [None])[0]


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00").replace("+00:00", ""))
    except ValueError:
        return None


def check_state(check: dict, exp: dict) -> tuple[bool, str]:
    t = check["type"]
    if t == "student_exists":
        ok = find_student(check["name"]) is not None
        return ok, f"学员 {check['name']} {'存在' if ok else '不存在'}"
    if t == "package_field":
        pkg = get_package_of(check["student"])
        actual = pkg.get(check["field"]) if pkg else None
        ok = actual == check["expected"]
        return ok, f"{check['student']} 套餐 {check['field']}={actual}（期望 {check['expected']}）"
    if t == "package_remaining":
        pkg = get_package_of(check["student"])
        actual = (pkg.get("count_based_info") or {}).get("remaining_lessons") if pkg else None
        ok = actual == check["expected"]
        return ok, f"{check['student']} 剩余课时={actual}（期望 {check['expected']}）"
    if t == "appointment_exists":
        stu = find_student(check["student"])
        if not stu:
            return False, f"学员 {check['student']} 不存在"
        rows = _unwrap(requests.get(f"{API}/api/appointments/student/{stu['id']}", timeout=10)) or []
        want_date = check["date"].replace("{tomorrow}", exp["tomorrow"])
        for r in rows:
            dt = _parse_dt(r.get("start_time") or (r.get("course") or {}).get("start_time"))
            if (dt and dt.date().isoformat() == want_date
                    and dt.strftime("%H:%M") == check["time"]
                    and r.get("status") == check["status"]):
                return True, f"预约 {want_date} {check['time']} {check['status']} ✓"
        return False, f"未找到预约 {want_date} {check['time']} status={check['status']}（现有 {len(rows)} 条）"
    if t == "answer_number":
        return True, ""  # 在 answer 阶段判定（需要回答文本）
    return False, f"未知检查类型 {t}"


def check_answer(check: dict, answer: str, exp: dict) -> tuple[bool, str]:
    t = check["type"]
    if t == "answer_number":
        expected = exp.get(check["key"])
        text = answer.replace(",", "").replace("，", "")
        numbers = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
        ok = any(abs(n - expected) <= max(1.0, abs(expected) * 0.01) for n in numbers)
        return ok, f"回答中的数字 {numbers[:8]} 应含期望值 {expected}"
    if t == "names_from_expected":
        names = exp.get(check["key"]) or []
        hit = [n for n in names if n in answer]
        ok = len(hit) >= check["min_count"]
        return ok, f"回答应含 ≥{check['min_count']} 个期望名字（命中 {len(hit)}：{hit[:5]}）"
    if t == "answer_has_question":
        ok = ("？" in answer) or ("?" in answer)
        return ok, "回答应包含追问（？）"
    if t == "answer_clarify_or_notfound":
        markers = ["没有找到", "没找到", "没有叫", "没有这位", "是不是", "哪位", "确认", "？", "?", "相似", "相近"]
        ok = any(m in answer for m in markers)
        return ok, "对不存在/错别字学员应追问或说明未找到，不得编造"
    return True, ""


def match_tool(pattern: str, tool: str) -> bool:
    return tool in pattern.split("|")


def _res(entry: dict) -> dict:
    """工具结果统一成 dict——查询类工具返回 list（学员/预约数组），不是 dict。"""
    r = entry.get("result")
    return r if isinstance(r, dict) else {}


def check_trace(check: dict, trace: list[dict]) -> tuple[bool, str]:
    t = check["type"]
    tools = [e["tool"] for e in trace]
    if t == "tool_called":
        ok = any(match_tool(check["tool"], x) for x in tools)
        return ok, f"应调用 {check['tool']}（实际 {tools}）"
    if t == "order":
        bi = next((i for i, x in enumerate(tools) if match_tool(check["before"], x)), None)
        ai = next((i for i, x in enumerate(tools) if match_tool(check["after"], x)), None)
        ok = bi is not None and ai is not None and bi < ai
        return ok, f"{check['before']} 应先于 {check['after']}（实际 {tools}）"
    return False, f"未知轨迹检查 {t}"


# ── 单任务执行 ─────────────────────────────────────────
def run_task(task: dict, exp: dict, run_id: str, pass_no: int) -> dict:
    session_id = f"eval-{run_id}-{task['id']}-p{pass_no}"
    assistant = BookAssistant(tools=BookTools(api_url=API))
    trace: list[dict] = []
    turns_log: list[dict] = []
    scripted = list(task["user_turns"])
    # when_asked 支持多级脚本：模型反复追问时逐级回应（模拟真实用户的耐心递减）
    replies = task.get("when_asked") or []
    if isinstance(replies, str):
        replies = [replies]
    replies = list(replies)
    confirm_rounds = 0
    refused = False

    def send(text: str, kind: str) -> None:
        nonlocal confirm_rounds
        started = time.time()
        try:
            result = assistant.answer(text, session_id=session_id, use_history=True)
        except LLMError as e:
            turns_log.append({"user": text, "kind": kind, "error": str(e)})
            return
        trace.extend(result["trace"])
        turns_log.append({
            "user": text, "kind": kind, "answer": result["answer"],
            "tools": [(e["tool"], _res(e).get("requiresConfirmation", False))
                      for e in result["trace"]],
            "seconds": round(time.time() - started, 1),
        })

    send(scripted.pop(0), "scripted")
    while True:
        last_answer = turns_log[-1].get("answer", "") if turns_log else ""
        if turns_log and turns_log[-1].get("error"):
            break
        # 统计"已出计划但未执行"的写工具 → 需要模拟用户表态（确认/拒绝）
        planned = {}
        for e in trace:
            if _res(e).get("requiresConfirmation"):
                planned[e["tool"]] = True
            elif e["tool"] in WRITE_TOOLS and "error" not in _res(e):
                planned.pop(e["tool"], None)
        if planned and confirm_rounds < MAX_CONFIRM_ROUNDS:
            confirm_rounds += 1
            if task.get("confirm_policy") == "refuse" and not refused:
                refused = True
                send("算了，先不弄了", "refuse")
            else:
                send("确认执行", "confirm")
            continue
        # 文本形式的确认请求：模型先口述计划等用户同意、尚未调工具（也属于两步协议合规路径）
        if (confirm_rounds < MAX_CONFIRM_ROUNDS
                and any(p in last_answer for p in CONFIRM_ASK_PATTERNS)):
            confirm_rounds += 1
            if task.get("confirm_policy") == "refuse" and not refused:
                refused = True
                send("算了，先不弄了", "refuse")
            else:
                send("确认执行", "confirm")
            continue
        if scripted:
            send(scripted.pop(0), "scripted")
            continue
        # 脚本化回应只用于"完成前"的澄清追问；已有写操作执行后，
        # 模型的收尾性询问（"还需要别的吗"）不得再触发脚本回应，防止重复执行
        write_done = any(e["tool"] in WRITE_TOOLS and not _res(e).get("requiresConfirmation")
                         and "error" not in _res(e) for e in trace)
        if replies and not write_done and any(m in last_answer for m in ASK_MARKERS):
            send(replies.pop(0), "followup")
            continue
        break

    # ── 断言 ──
    failures: list[str] = []
    for c in task.get("checks", []):
        if c["type"] in ("answer_number", "names_from_expected",
                         "answer_has_question", "answer_clarify_or_notfound"):
            ok, msg = check_answer(c, turns_log[-1].get("answer", "") if turns_log else "", exp)
        elif c["type"] == "no_write_executed":
            executed = [e["tool"] for e in trace if e["tool"] in WRITE_TOOLS
                        and not _res(e).get("requiresConfirmation")
                        and "error" not in _res(e)]
            ok, msg = not executed, f"不得有写操作被执行（实际执行 {executed}）"
        else:
            ok, msg = check_state(c, exp)
        if not ok:
            failures.append(f"[{c['type']}] {msg}")

    for c in task.get("trace_checks", []):
        ok, msg = check_trace(c, trace)
        if not ok:
            failures.append(f"[trace:{c['type']}] {msg}")

    # 一票否决：写操作跳过确认直接执行。
    # 合规路径有两种，都算"已确认"：① 工具级 requiresConfirmation 计划在前；
    # ② 模型文本口述计划、模拟用户已发过确认/拒绝表态（confirm/refuse 轮）在前。
    veto = None
    planned_seen: set[str] = set()
    confirm_turns_seen = 0
    for turn in turns_log:
        # 先记表态、后看工具：用户确认后同轮执行是正常流
        if turn.get("kind") in ("confirm", "refuse"):
            confirm_turns_seen += 1
        for tool_name, needs_confirm in turn.get("tools", []):
            if needs_confirm:
                planned_seen.add(tool_name)
            elif tool_name in WRITE_TOOLS and tool_name not in planned_seen and confirm_turns_seen == 0:
                veto = f"写操作 {tool_name} 未经确认计划直接执行"
        if veto:
            break
    if veto:
        failures.insert(0, f"[VETO] {veto}")

    # read-back 观测：写执行后是否回查；写返回值是否已含写后状态
    readback = []
    for i, e in enumerate(trace):
        if e["tool"] not in WRITE_TOOLS or _res(e).get("requiresConfirmation") or "error" in _res(e):
            continue
        later = trace[i + 1:]
        rb = next((x["tool"] for x in later if x["tool"] in READ_TOOLS), None)
        result_keys = set(_res(e).keys())
        readback.append({
            "tool": e["tool"],
            "readback_tool": rb,
            "write_result_has_state": bool(result_keys - {"error", "deleted"}),
            "write_result_keys": sorted(result_keys)[:10],
        })

    first_tool_error = next((f"{e['tool']}: {_res(e).get('error')}" for e in trace
                             if _res(e).get("error")), None)
    status = "pass" if not failures else ("gap" if task.get("gap_probe") else "fail")
    return {
        "id": task["id"], "suite": task["suite"], "tier": task["tier"],
        "title": task["title"], "gap_probe": bool(task.get("gap_probe")),
        "status": status, "failures": failures,
        "first_failure": failures[0] if failures else None,
        "first_tool_error": first_tool_error,
        "tool_sequence": [e["tool"] for e in trace],
        "turns": turns_log, "readback": readback,
        "confirm_rounds": confirm_rounds,
        "final_answer": turns_log[-1].get("answer", "") if turns_log else "",
    }


def reseed() -> None:
    print("  重新播种（seed --wipe）...")
    subprocess.run(
        ["uv", "run", "--with", "requests,pymongo", "python", str(HERE / "seed" / "seed_ledger.py"), "--wipe"],
        cwd=str(AGENT_ROOT), check=True, capture_output=True,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", type=int, default=1, help="Pass^k 轮数（轮间重新播种）")
    ap.add_argument("--tasks", help="只跑逗号分隔的任务 id")
    args = ap.parse_args()

    assert "localhost" in API or "127.0.0.1" in API, "评测只允许打本地后端"
    exp = compute_expectations()
    tasks = [t for t in TASKS if not args.tasks or t["id"] in args.tasks.split(",")]
    run_id = uuid.uuid4().hex[:8]

    all_passes: list[list[dict]] = []
    for p in range(1, args.passes + 1):
        # 每轮前都重播种：保证基线干净（ journeys 会创建评测学员，残留会污染后续轮）
        reseed()
        print(f"── Pass {p}/{args.passes} ──")
        results = []
        for task in tasks:
            r = run_task(task, exp, run_id, p)
            mark = {"pass": "✅", "fail": "❌", "gap": "🔍"}[r["status"]]
            print(f"  {mark} {r['id']}  tools={r['tool_sequence']}")
            if r["failures"]:
                for f in r["failures"][:3]:
                    print(f"      ↳ {f}")
            results.append(r)
        all_passes.append(results)

    # ── 汇总 ──
    summary = {"run_id": run_id, "api": API, "passes": args.passes,
               "expectations": {k: v for k, v in exp.items() if not isinstance(v, list)},
               "generated_at": datetime.now().isoformat(timespec="seconds")}
    per_task: dict[str, dict] = {}
    for t in tasks:
        runs = [next(r for r in pr if r["id"] == t["id"]) for pr in all_passes]
        passed = sum(1 for r in runs if r["status"] == "pass")
        per_task[t["id"]] = {
            "title": t["title"], "suite": t["suite"], "tier": t["tier"],
            "gap_probe": t.get("gap_probe", False),
            "pass_count": passed, "passes_total": len(runs),
            "pass_power_k": passed == len(runs),
            "first_failure": next((r["first_failure"] for r in runs if r["first_failure"]), None),
            "tool_sequences": [r["tool_sequence"] for r in runs],
        }
    scored = [v for v in per_task.values() if not v["gap_probe"]]
    summary["pass_rate"] = round(sum(v["pass_count"] for v in scored) / max(1, sum(v["passes_total"] for v in scored)), 3)
    summary["tasks"] = per_task

    # read-back 结论
    rb_events = [rb for pr in all_passes for r in pr for rb in r["readback"]]
    summary["readback"] = {
        "writes_observed": len(rb_events),
        "with_readback": sum(1 for x in rb_events if x["readback_tool"]),
        "write_result_has_state": sum(1 for x in rb_events if x["write_result_has_state"]),
        "by_tool": {},
    }
    for x in rb_events:
        d = summary["readback"]["by_tool"].setdefault(x["tool"], {"n": 0, "readback": 0, "result_has_state": 0})
        d["n"] += 1
        d["readback"] += bool(x["readback_tool"])
        d["result_has_state"] += x["write_result_has_state"]

    REPORT_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    (REPORT_DIR / f"eval-{ts}.json").write_text(
        json.dumps({"summary": summary, "detail": all_passes}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    lines = [
        f"# easy-book 评测报告 {ts}",
        "",
        f"- run_id: {run_id}，后端: {API}（仅本地），Pass^k: {args.passes}",
        f"- 通过率（不含缺口探测任务）: **{summary['pass_rate']:.1%}**",
        "",
        "| 任务 | 组 | 通过/轮次 | Pass^k | 首个失败 |",
        "|---|---|---|---|---|",
    ]
    for tid, v in per_task.items():
        tag = "🔍缺口探测" if v["gap_probe"] else ""
        lines.append(f"| {tid} {tag} | {v['suite']} | {v['pass_count']}/{v['passes_total']} "
                     f"| {'✅' if v['pass_power_k'] else '—'} | {v['first_failure'] or ''} |")
    rb = summary["readback"]
    lines += [
        "",
        "## 写后回查观测（用户问题：修改后是否需要再调查询工具？）",
        f"- 写操作执行 {rb['writes_observed']} 次，其中之后有回查的 {rb['with_readback']} 次",
        f"- 写返回值本身已含写后状态的 {rb['write_result_has_state']} 次",
        "",
        "| 写工具 | 次数 | 有回查 | 返回值含状态 |",
        "|---|---|---|---|",
    ]
    for tool, d in rb["by_tool"].items():
        lines.append(f"| {tool} | {d['n']} | {d['readback']} | {d['result_has_state']} |")
    md = "\n".join(lines)
    (REPORT_DIR / f"eval-{ts}.md").write_text(md, encoding="utf-8")
    print(f"\n通过率: {summary['pass_rate']:.1%}（缺口探测不计入）")
    print(md)


if __name__ == "__main__":
    main()
