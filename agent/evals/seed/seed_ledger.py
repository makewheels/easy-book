"""把台账解析结果导入 easy-book 本地 dev 后端（评测基线数据）。

用法：
  uv run --with requests,pymongo python seed_ledger.py           # 首次导入
  uv run --with requests,pymongo python seed_ledger.py --wipe    # 清空本地库重导

导入链路（全部走真实 API，考勤经 预约→签到 真实扣减）：
  POST /api/students/ → POST /api/packages/（remaining=total）
  → 每条考勤 POST /api/appointments/ + POST /api/attendance/checkin（扣 1 节）
  → pymongo 回溯 packages/students.create_time 到首次上课日（利润统计按套餐创建时间，
    回溯后"近三个月营收"才有真实月度分布）

安全护栏：硬编码只打 localhost:8002 + 本地 easy_book_dev 库，绝不触碰生产。
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bson import ObjectId
from pymongo import MongoClient

HERE = Path(__file__).resolve().parent
PARSED = HERE / "data" / "ledger_parsed.json"
REPORT_DIR = HERE.parent / "reports"

API = "http://localhost:8002"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "easy_book_dev"
DEFAULT_TIME = "14:00"  # 台账未记时间的考勤统一按下午首场导入（报告中已标注时间为推断值）


def _unwrap(resp: requests.Response) -> dict:
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict) and "code" in data and "data" in data:
        if data.get("code") != 200:
            raise RuntimeError(data.get("message", "请求失败"))
        return data.get("data") or {}
    return data or {}


def wipe(client: MongoClient) -> None:
    db = client[DB_NAME]
    for coll in ("students", "packages", "appointments", "courses", "attendance"):
        db[coll].delete_many({})
    print(f"已清空 {DB_NAME} 的 students/packages/appointments/courses/attendance")


def main() -> None:  # noqa: C901, PLR0912, PLR0915
    parser = argparse.ArgumentParser()
    parser.add_argument("--wipe", action="store_true", help="导入前清空本地 dev 库")
    args = parser.parse_args()

    assert "localhost" in API, "种子导入只允许打本地后端"
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]

    if db.students.count_documents({}) > 0:
        if not args.wipe:
            sys.exit("本地库已有数据：加 --wipe 清空重导，或换一个 DB_NAME")
        wipe(client)

    data = json.loads(PARSED.read_text(encoding="utf-8"))
    students = data["students"]
    report = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "api": API, "db": DB_NAME,
        "students": [], "failures": [],
        "totals": {"students": 0, "packages": 0, "appointments": 0, "checkins": 0},
    }

    for idx, s in enumerate(students, 1):
        name = s["name"]
        att = s["attendance"]
        try:
            stu = _unwrap(requests.post(f"{API}/api/students/", json={"name": name}, timeout=10))
            student_id = stu.get("id") or stu.get("_id")
            if not student_id:
                raise RuntimeError(f"创建学员响应缺 id: {stu}")

            pkg_id = None
            total = max(s["package"]["count"] or 0, len(att))
            price = s["package"]["price"] or 0
            if total > 0:
                # 后端要求 price>0：台账未记金额的按 1 元占位、包名打标，报告中可识别剔除
                real_price = price > 0
                pkg = _unwrap(requests.post(f"{API}/api/packages/", json={
                    "student_id": student_id,
                    "name": "台账导入课包" if real_price else "台账导入课包(价格未记账)",
                    "package_type": "count_based",
                    "price": price if real_price else 1.0,
                    "venue_share": 0,
                    "count_based_info": {"total_lessons": total, "remaining_lessons": total},
                }, timeout=10))
                pkg_id = pkg.get("id") or pkg.get("_id")
                report["totals"]["packages"] += 1
            imported_price = (price if price > 0 else 1.0) if total > 0 else 0

            ok, skipped = 0, []
            for a in att:
                time_str = a["time"] or DEFAULT_TIME
                start = f"{a['date']}T{time_str}:00"
                try:
                    appt = _unwrap(requests.post(f"{API}/api/appointments/", json={
                        "student_id": student_id,
                        "start_time": start,
                        "duration_in_minutes": 60,
                    }, timeout=10))
                    appt_id = appt.get("id") or appt.get("_id")
                    report["totals"]["appointments"] += 1
                    _unwrap(requests.post(f"{API}/api/attendance/checkin", json={
                        "appointment_id": appt_id,
                        "student_id": student_id,
                    }, timeout=10))
                    report["totals"]["checkins"] += 1
                    ok += 1
                except Exception as e:  # 冲突/脏日期：记录不中断
                    skipped.append({"raw": a["raw"], "date": a["date"], "error": str(e)})

            report["students"].append({
                "name": name, "student_id": student_id, "package_id": pkg_id,
                "graduated": s["graduated"], "price": price,
                "imported_price": imported_price, "total": total,
                "attendance_ok": ok, "attendance_skipped": skipped,
            })
            report["totals"]["students"] += 1
            if skipped:
                report["failures"].append({"student": name, "skipped": skipped})
            if idx % 20 == 0:
                print(f"  进度 {idx}/{len(students)}")
        except Exception as e:
            report["failures"].append({"student": name, "error": str(e)})

    # 回溯创建时间：套餐/学员的 create_time = 首次上课日（利润统计口径=套餐创建时间）
    # 注意 Mongo _id 是 ObjectId，API 返回的是其字符串形式，需转回再匹配
    first_date = {s["name"]: s["attendance"][0]["date"] for s in students if s["attendance"]}
    backdated = 0
    for item in report["students"]:
        first = first_date.get(item["name"])
        if not first:
            continue
        created = datetime.fromisoformat(first).replace(hour=10)
        if item["package_id"]:
            r = db.packages.update_one({"_id": ObjectId(item["package_id"])},
                                       {"$set": {"create_time": created}})
            backdated += r.matched_count
        db.students.update_one({"_id": ObjectId(item["student_id"])},
                               {"$set": {"create_time": created}})
    report["backdated_packages"] = backdated

    # 校验：营收合计 + 抽样剩余课时
    profit = _unwrap(requests.get(f"{API}/api/stats/profit", timeout=10))
    expected_revenue = sum(i["imported_price"] for i in report["students"])
    window_start = (datetime.now() - timedelta(days=90)).date().isoformat()
    profit_window = _unwrap(requests.get(
        f"{API}/api/stats/profit", params={"start_date": window_start}, timeout=10))
    report["verify"] = {
        "profit_total_revenue": profit.get("total_revenue"),
        "expected_revenue": expected_revenue,
        "revenue_match": profit.get("total_revenue") == expected_revenue,
        "revenue_last_90d": profit_window.get("total_revenue"),
        "packages_last_90d": profit_window.get("package_count"),
    }
    sample = next((i for i in report["students"] if i["package_id"] and i["total"]), None)
    if sample:
        pkg = _unwrap(requests.get(f"{API}/api/packages/{sample['package_id']}", timeout=10))
        cbi = pkg.get("count_based_info") or {}
        expected_remaining = sample["total"] - sample["attendance_ok"]
        report["verify"]["sample"] = {
            "name": sample["name"],
            "remaining": cbi.get("remaining_lessons"),
            "expected": expected_remaining,
            "match": cbi.get("remaining_lessons") == expected_remaining,
        }

    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "seed_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 台账导入核对报告",
        "",
        f"- 时间：{report['started_at']}，目标：{report['api']} / {report['db']}（仅本地）",
        f"- 学员 {report['totals']['students']}，课包 {report['totals']['packages']}，"
        f"预约 {report['totals']['appointments']}，签到扣减 {report['totals']['checkins']}",
        f"- create_time 回溯 {backdated} 个课包（首次上课日 10:00）",
        "",
        "## 校验",
        f"- 营收合计：{report['verify']['profit_total_revenue']}"
        f"（期望 {expected_revenue}）→ {'✅' if report['verify']['revenue_match'] else '❌'}",
    ]
    if report["verify"].get("sample"):
        sm = report["verify"]["sample"]
        lines.append(f"- 抽样 {sm['name']}：剩余 {sm['remaining']}"
                     f"（期望 {sm['expected']}）→ {'✅' if sm['match'] else '❌'}")
    if report["failures"]:
        lines += ["", f"## 跳过/失败（{len(report['failures'])} 名学员）"]
        for f in report["failures"][:20]:
            lines.append(f"- {json.dumps(f, ensure_ascii=False)}")
    else:
        lines += ["", "## 跳过/失败：无"]
    lines += [
        "",
        "## 清洗口径（详见 ledger_parsed.json 的 conventions/warnings）",
        "- 年份：11/12月→2025，其余→2026；整列无月份按块内众数兜底",
        "- 时间：小时≤8 按下午场+12（推断值，日期忠实）；未记时间统一 14:00",
        "- 课包：台账无分成记录，venue_share 统一 0；无节数记录时总数=考勤次数",
        "- 台账未记金额的课包按 1 元占位、包名带(价格未记账)——后端要求 price>0",
        "- 冯文钰等无考勤学员不建课包（真实场景：已登记未上课）",
    ]
    (REPORT_DIR / "seed_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n完成：{json.dumps(report['totals'], ensure_ascii=False)}")
    print(f"校验：{json.dumps(report['verify'], ensure_ascii=False)}")
    print(f"报告：{REPORT_DIR / 'seed_report.md'}")


if __name__ == "__main__":
    main()
