"""Easy-Book 工具执行层。

模式与 video-2022 的 VideoTools 一致：
- 工具名 == 方法名，execute() 用 getattr 分发，没有注册器
- 写操作默认返回 {"requiresConfirmation": True, "planned": {...}}，
  confirm_write=True 时才真正执行
- 异常永不抛给 agent loop，统一转成 {"error": ...} 返回值
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

import requests

from .schema import WRITE_TOOLS
from . import trace as lf_trace


@dataclass
class BookTools:
    """Easy-Book 后端 REST API 的工具封装。"""

    api_url: str = "http://localhost:8002"
    confirm_write: bool = False
    timeout: float = 15.0

    # 每次 execute 的记录，便于 agent 输出调用轨迹
    trace: list[dict[str, Any]] = field(default_factory=list)

    # ── 基础设施 ────────────────────────────────────────────────

    def _url(self, path: str) -> str:
        return f"{self.api_url.rstrip('/')}{path}"

    def _request(self, method: str, path: str, *, json_body: Any = None, params: Optional[dict] = None) -> Any:
        """发请求并统一拆信封：{code,message,data} → data；裸对象原样返回。"""
        resp = requests.request(
            method,
            self._url(path),
            json=json_body,
            params=params,
            timeout=self.timeout,
        )
        if resp.status_code == 204:
            return {"deleted": True}
        if resp.status_code >= 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except ValueError:
                detail = resp.text
            raise RuntimeError(f"HTTP {resp.status_code}: {detail}")

        data = resp.json()
        # appointments/courses/attendance/stats 接口带 {code,message,data} 信封
        if isinstance(data, dict) and "code" in data and "data" in data:
            if data.get("code") != 200:
                raise RuntimeError(data.get("message", "请求失败"))
            return data.get("data")
        return data

    def execute(self, name: str, args: dict) -> Any:
        """agent loop 的唯一入口：按名字分发到同名方法。"""
        method = getattr(self, name, None)
        if method is None or name.startswith("_"):
            return {"error": f"Unknown tool: {name}"}
        span = lf_trace.start_tool_span(name, args)
        started = time.time()
        try:
            if name in WRITE_TOOLS and not (self.confirm_write or args.get("confirm")):
                planned = {k: v for k, v in args.items() if k != "confirm"}
                result: Any = {"requiresConfirmation": True, "tool": name, "planned": planned}
            else:
                result = method(**args)
        except TypeError as exc:
            result = {"error": f"参数错误: {exc}", "tool": name}
        except Exception as exc:  # noqa: BLE001 — 错误转返回值是约定
            result = {"error": str(exc), "tool": name}
        lf_trace.finish_tool_span(span, result=result)
        self._record(name, args, result, time.time() - started)
        return result

    def _record(self, name: str, args: dict, result: Any, elapsed: float) -> None:
        self.trace.append({
            "tool": name,
            "args": args,
            "result": result,
            "elapsed_seconds": round(elapsed, 3),
        })

    # ── 查询：学员 ──────────────────────────────────────────────

    def search_students(self, search: Optional[str] = None, limit: int = 50) -> Any:
        params: dict[str, Any] = {"limit": limit}
        if search:
            params["search"] = search
        return self._request("GET", "/api/students/", params=params)

    def get_student(self, student_id: str) -> Any:
        return self._request("GET", f"/api/students/{student_id}")

    # ── 查询：日程/预约 ─────────────────────────────────────────

    def get_schedule(self, date: str) -> Any:
        return self._request("GET", f"/api/appointments/daily/{date}")

    def get_schedule_range(self, start_date: str, end_date: str) -> Any:
        return self._request(
            "GET", "/api/appointments/batch",
            params={"start_date": start_date, "end_date": end_date},
        )

    def list_student_appointments(self, student_id: str, status: Optional[str] = None) -> Any:
        params = {"status": status} if status else None
        return self._request("GET", f"/api/appointments/student/{student_id}", params=params)

    # ── 查询：套餐/财务 ─────────────────────────────────────────

    def list_student_packages(self, student_id: str) -> Any:
        return self._request("GET", f"/api/packages/student/{student_id}")

    def get_package(self, package_id: str) -> Any:
        return self._request("GET", f"/api/packages/{package_id}")

    def profit_stats(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Any:
        params: dict[str, str] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._request("GET", "/api/stats/profit", params=params or None)

    def lessons_overview(self) -> Any:
        return self._request("GET", "/api/stats/lessons")

    # ── 写操作：学员 ────────────────────────────────────────────

    def create_student(
        self,
        name: str,
        gender: Optional[str] = None,
        age: Optional[int] = None,
        phone: Optional[str] = None,
        emergency_contact: Optional[str] = None,
        confirm: bool = False,
    ) -> Any:
        body: dict[str, Any] = {"name": name}
        for key, val in (("gender", gender), ("age", age), ("phone", phone),
                         ("emergency_contact", emergency_contact)):
            if val is not None:
                body[key] = val
        return self._request("POST", "/api/students/", json_body=body)

    def update_student(
        self,
        student_id: str,
        name: Optional[str] = None,
        gender: Optional[str] = None,
        age: Optional[int] = None,
        phone: Optional[str] = None,
        emergency_contact: Optional[str] = None,
    
                                                                                                                                                                                                                                                              confirm: bool = False,
    ) -> Any:
        body: dict[str, Any] = {}
        for key, val in (("name", name), ("gender", gender), ("age", age),
                         ("phone", phone), ("emergency_contact", emergency_contact)):
            if val is not None:
                body[key] = val
        if not body:
            raise ValueError("没有提供要修改的字段")
        return self._request("PUT", f"/api/students/{student_id}", json_body=body)

    def delete_student(self, student_id: str, confirm: bool = False) -> Any:
        return self._request("DELETE", f"/api/students/{student_id}")

    # ── 写操作：套餐 ────────────────────────────────────────────

    def create_package(
        self,
        student_id: str,
        name: str,
        package_type: str,
        price: float,
        venue_share: float,
        total_lessons: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    
                                                                                                                                                                                                                                                                                          confirm: bool = False,
    ) -> Any:
        body: dict[str, Any] = {
            "student_id": student_id,
            "name": name,
            "package_type": package_type,
            "price": price,
            "venue_share": venue_share,
        }
        if package_type == "time_based":
            info: dict[str, Any] = {}
            if start_date:
                info["start_date"] = start_date
            if end_date:
                info["end_date"] = end_date
            body["time_based_info"] = info
        else:
            if not total_lessons:
                raise ValueError("记次套餐必须提供 total_lessons（总课时）")
            body["count_based_info"] = {
                "total_lessons": total_lessons,
                "remaining_lessons": total_lessons,
            }
        return self._request("POST", "/api/packages/", json_body=body)

    def update_package(
        self,
        package_id: str,
        name: Optional[str] = None,
        package_type: Optional[str] = None,
        price: Optional[float] = None,
        venue_share: Optional[float] = None,
    
                                                                                                                                                                                                                               confirm: bool = False,
    ) -> Any:
        body: dict[str, Any] = {}
        for key, val in (("name", name), ("package_type", package_type),
                         ("price", price), ("venue_share", venue_share)):
            if val is not None:
                body[key] = val
        if not body:
            raise ValueError("没有提供要修改的字段")
        return self._request("PUT", f"/api/packages/{package_id}", json_body=body)

    def adjust_package_lessons(
        self,
        package_id: str,
        delta: int,
        adjust_total: bool = False,
        reason: Optional[str] = None,
    
                                                                                                                                                                 confirm: bool = False,
    ) -> Any:
        body: dict[str, Any] = {"delta": delta, "adjust_total": adjust_total}
        if reason:
            body["reason"] = reason
        return self._request("POST", f"/api/packages/{package_id}/adjust-lessons", json_body=body)

    def delete_package(self, package_id: str, confirm: bool = False) -> Any:
        return self._request("DELETE", f"/api/packages/{package_id}")

    # ── 写操作：预约/考勤 ───────────────────────────────────────

    def book_appointment(self, student_id: str, start_time: str, duration_minutes: int = 60, confirm: bool = False) -> Any:
        return self._request("POST", "/api/appointments/", json_body={
            "student_id": student_id,
            "start_time": start_time,
            "duration_in_minutes": duration_minutes,
        })

    def cancel_appointment(self, appointment_id: str, confirm: bool = False) -> Any:
        return self._request("POST", f"/api/appointments/{appointment_id}/cancel")

    def checkin_appointment(self, appointment_id: str, student_id: str, confirm: bool = False) -> Any:
        return self._request("POST", "/api/attendance/checkin", json_body={
            "appointment_id": appointment_id,
            "student_id": student_id,
        })

    def set_appointment_status(self, appointment_id: str, status: str, confirm: bool = False) -> Any:
        return self._request("PUT", f"/api/appointments/{appointment_id}", json_body={"status": status})
