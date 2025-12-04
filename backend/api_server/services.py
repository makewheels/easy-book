from typing import List, Optional, Union
from datetime import datetime, date, timedelta
from api_server.models import StudentModel, AppointmentModel, AttendanceModel
from api_server.database import get_database

def calculate_dynamic_status_new(start_time: datetime, end_time: datetime, db_status: str) -> str:
    """
    根据当前时间和新的时间结构动态计算状态

    Args:
        start_time: 课程开始时间
        end_time: 课程结束时间
        db_status: 数据库中的状态 (scheduled, checked, cancel)

    Returns:
        动态状态 (scheduled, active, completed, checked, cancel)
    """
    # 如果已经签到或取消，保持原状态
    if db_status in ["checked", "cancel"]:
        return db_status

    # 如果是scheduled状态，需要判断时间
    # 确保使用naive datetime进行比较
    if start_time.tzinfo is not None:
        start_time = start_time.replace(tzinfo=None)
    if end_time.tzinfo is not None:
        end_time = end_time.replace(tzinfo=None)

    now = datetime.now()

    if now < start_time:
        # 还未到上课时间，显示为scheduled（蓝色）
        return "scheduled"
    elif now < end_time:
        # 正在上课时间，显示为active（进行中）
        return "active"
    else:
        # 已经过了上课时间，显示为completed（已完成）
        return "completed"

def calculate_dynamic_status(db_status: str, appointment_date: Union[date, str], time_slot: str) -> str:
    """
    根据当前时间和预约时间动态计算状态（兼容旧版本）

    Args:
        db_status: 数据库中的状态 (scheduled, checked, cancel)
        appointment_date: 预约日期
        time_slot: 时间段 (例如: "10:00")

    Returns:
        动态状态 (scheduled, active, completed, checked, cancel)
    """
    # 如果已经签到或取消，保持原状态
    if db_status in ["checked", "cancel"]:
        return db_status

    # 如果是scheduled状态，需要判断时间
    now = datetime.now()

    # 解析日期
    if isinstance(appointment_date, str):
        try:
            appointment_date_obj = date.fromisoformat(appointment_date)
        except ValueError:
            return db_status
    else:
        appointment_date_obj = appointment_date

    # 解析时间段
    try:
        hour, minute = map(int, time_slot.split(":"))
        appointment_datetime = datetime.combine(appointment_date_obj, datetime.min.time().replace(hour=hour, minute=minute))
    except (ValueError, AttributeError):
        # 如果时间解析失败，返回原状态
        return db_status

    # 判断时间状态
    class_end_time = appointment_datetime + timedelta(hours=1)

    if now < appointment_datetime:
        # 还未到上课时间，显示为scheduled（蓝色）
        return "scheduled"
    elif now < class_end_time:
        # 正在上课时间，显示为active（进行中）
        return "active"
    else:
        # 已经过了上课时间，显示为completed（已完成）
        return "completed"

def convert_legacy_time_data(appointment_data: dict) -> dict:
    """
    转换旧格式的时间数据为新格式

    Args:
        appointment_data: 包含 appointment_date 和 time_slot 的数据

    Returns:
        包含 start_time 和 end_time 的数据
    """
    appointment_date = appointment_data.get("appointment_date")
    time_slot = appointment_data.get("time_slot")

    if not appointment_date or not time_slot:
        return appointment_data

    # 如果已经有 start_time 和 end_time，不需要转换
    if "start_time" in appointment_data and "end_time" in appointment_data:
        return appointment_data

    # 解析日期
    if isinstance(appointment_date, str):
        try:
            appointment_date_obj = date.fromisoformat(appointment_date)
        except ValueError:
            return appointment_data
    else:
        appointment_date_obj = appointment_date

    # 解析时间
    try:
        hour, minute = map(int, time_slot.split(":"))
        start_datetime = datetime.combine(appointment_date_obj, datetime.min.time().replace(hour=hour, minute=minute))
        end_datetime = start_datetime + timedelta(hours=1)  # 默认1小时

        # 添加新字段
        appointment_data["start_time"] = start_datetime
        appointment_data["end_time"] = end_datetime

    except (ValueError, AttributeError):
        pass

    return appointment_data

class StudentService:
    @staticmethod
    async def create(student_data: dict) -> StudentModel:
        db = get_database()
        
        # 计算利润
        profit = student_data["price"] - student_data["venue_share"]
        student_data["profit"] = profit
        student_data["remaining_lessons"] = student_data["total_lessons"]
        
        student_id = await db.create_student(student_data)
        student_data["_id"] = student_id
        student_data["id"] = student_id
        
        return StudentModel(**student_data)
    
    @staticmethod
    def _prepare_student_data(student_data: dict) -> dict:
        """为学员数据提供默认值"""
        if student_data.get('remaining_lessons') is None:
            student_data['remaining_lessons'] = student_data.get('total_lessons', 0)

        if student_data.get('profit') is None:
            student_data['profit'] = student_data.get('price', 0) - student_data.get('venue_share', 0)

        return student_data

    @staticmethod
    async def get_all(skip: int = 0, limit: int = 20) -> List[StudentModel]:
        db = get_database()
        students = await db.get_students()
        # 简单分页
        students = students[skip:skip+limit]
        processed_students = []
        for student in students:
            student = StudentService._prepare_student_data(student.copy())
            processed_students.append(StudentModel(**student))
        return processed_students
    
    @staticmethod
    async def get_by_id(student_id: str) -> Optional[StudentModel]:
        db = get_database()
        student = await db.get_student(student_id)
        if student:
            student = StudentService._prepare_student_data(student)
            return StudentModel(**student)
        return None
    
    @staticmethod
    async def update(student_id: str, update_data: dict) -> Optional[StudentModel]:
        db = get_database()
        success = await db.update_student(student_id, update_data)
        if success:
            return await StudentService.get_by_id(student_id)
        return None
    
    @staticmethod
    async def delete(student_id: str) -> bool:
        db = get_database()
        return await db.delete_student(student_id)
    
    @staticmethod
    async def update_lessons(student_id: str, new_lessons: int) -> bool:
        db = get_database()
        return await db.update_student(student_id, {"remaining_lessons": new_lessons})

class AppointmentService:
    @staticmethod
    async def create(appointment_data: dict) -> AppointmentModel:
        db = get_database()

        # 处理新旧格式的时间数据
        if "start_time" in appointment_data and "end_time" in appointment_data:
            # 新格式：使用 start_time 和 end_time
            start_time = appointment_data["start_time"]
            end_time = appointment_data["end_time"]

            # 验证时间格式
            if not isinstance(start_time, datetime):
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                    appointment_data["start_time"] = start_time
                else:
                    raise ValueError("start_time 格式错误")

            if not isinstance(end_time, datetime):
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time)
                    appointment_data["end_time"] = end_time
                else:
                    raise ValueError("end_time 格式错误")

            # 验证时间逻辑
            if start_time >= end_time:
                raise ValueError("开始时间必须早于结束时间")

            # 检查时间冲突（新格式）
            await AppointmentService.check_time_conflict(
                appointment_data["student_id"],
                start_time,
                end_time
            )

            # 为了兼容性，同时保存旧格式字段
            appointment_data["appointment_date"] = start_time.date().isoformat()
            appointment_data["time_slot"] = start_time.strftime("%H:%M")

        else:
            # 旧格式：使用 appointment_date 和 time_slot
            appointment_date = appointment_data["appointment_date"]
            time_slot = appointment_data["time_slot"]

            # 处理日期格式（确保统一存储为字符串）
            if isinstance(appointment_date, date):
                appointment_data["appointment_date"] = appointment_date.isoformat()

            # 检查时间冲突（旧格式）
            await AppointmentService.check_conflict(
                appointment_data["student_id"],
                appointment_date,
                time_slot
            )

            # 转换为新格式
            appointment_data = convert_legacy_time_data(appointment_data)

        # 获取学员信息，检查剩余课程
        student = await db.get_student(appointment_data["student_id"])
        if not student:
            raise ValueError("学员不存在")

        remaining_lessons = student.get("remaining_lessons", 0)
        if remaining_lessons <= 0:
            raise ValueError("学员剩余课程不足，无法预约")

        # 扣减课程次数
        new_remaining_lessons = remaining_lessons - 1
        await db.update_student(appointment_data["student_id"], {
            "remaining_lessons": new_remaining_lessons,
            "update_time": datetime.utcnow()
        })

        # 设置创建和更新时间
        appointment_data["create_time"] = datetime.utcnow()
        appointment_data["update_time"] = datetime.utcnow()

        # 创建预约
        appointment_id = await db.create_appointment(appointment_data)
        appointment_data["_id"] = appointment_id
        appointment_data["id"] = appointment_id

        return AppointmentModel(**appointment_data)
    
    @staticmethod
    async def check_time_conflict(student_id: str, start_time: datetime, end_time: datetime):
        """
        检查新格式的时间冲突

        Args:
            student_id: 学员ID
            start_time: 开始时间
            end_time: 结束时间
        """
        db = get_database()

        # 获取学员信息
        student = await db.get_student(student_id)
        if not student:
            raise ValueError("学员不存在")

        # 检查同一个学员是否已经在同一时间预约
        appointments = await db.get_appointments()
        for apt in appointments:
            if apt.get("status") == "cancel":
                continue

            # 获取预约的时间信息
            apt_start_time = apt.get("start_time")
            apt_end_time = apt.get("end_time")

            # 如果新格式时间不存在，尝试从旧格式转换
            if not apt_start_time or not apt_end_time:
                apt = convert_legacy_time_data(apt.copy())
                apt_start_time = apt.get("start_time")
                apt_end_time = apt.get("end_time")

            if not apt_start_time or not apt_end_time:
                continue

            # 确保时间格式正确
            if isinstance(apt_start_time, str):
                apt_start_time = datetime.fromisoformat(apt_start_time)
            if isinstance(apt_end_time, str):
                apt_end_time = datetime.fromisoformat(apt_end_time)

            # 检查时间重叠：A.start < B.end AND A.end > B.start
            if (start_time < apt_end_time and end_time > apt_start_time):
                # 如果是同一个学员，直接报错
                if apt.get("student_id") == student_id:
                    raise ValueError(f"您在该时间段已有预约：{apt_start_time.strftime('%H:%M')}-{apt_end_time.strftime('%H:%M')}")

                # 如果是1v1课程，检查与其他学员的冲突
                if student["package_type"] == "1v1":
                    # 检查冲突学员是否也是1v1
                    conflict_student = await db.get_student(apt.get("student_id"))
                    if conflict_student and conflict_student["package_type"] == "1v1":
                        raise ValueError(f"该时间段已被其他1v1预约占用：{apt_start_time.strftime('%H:%M')}-{apt_end_time.strftime('%H:%M')}")

    @staticmethod
    async def check_conflict(student_id: str, appointment_date, time_slot: str):
        """
        检查旧格式的时间冲突（兼容性方法）

        Args:
            student_id: 学员ID
            appointment_date: 预约日期
            time_slot: 时间段
        """
        db = get_database()

        # 处理日期格式（支持字符串和date对象）
        if isinstance(appointment_date, str):
            appointment_date_obj = date.fromisoformat(appointment_date)
        else:
            appointment_date_obj = appointment_date

        # 获取学员信息
        student = await db.get_student(student_id)
        if not student:
            raise ValueError("学员不存在")

        # 检查同一个学员是否已经在同一时间预约
        appointments = await db.get_appointments()
        for apt in appointments:
            if (apt.get("appointment_date") == appointment_date_obj.isoformat() and
                apt.get("time_slot") == time_slot and
                apt.get("status") != "cancel"):

                # 如果是同一个学员，直接报错
                if apt.get("student_id") == student_id:
                    raise ValueError(f"您已经在 {time_slot} 预约了课程")

                # 如果是1v1课程，检查与其他学员的冲突
                if student["package_type"] == "1v1":
                    # 检查冲突学员是否也是1v1
                    conflict_student = await db.get_student(apt.get("student_id"))
                    if conflict_student and conflict_student["package_type"] == "1v1":
                        raise ValueError(f"时间段 {time_slot} 已有其他1v1预约")
    
    @staticmethod
    async def get_by_student(student_id: str, future_only: bool = False) -> List[AppointmentModel]:
        db = get_database()
        appointments = await db.get_student_appointments(student_id)
        
        if future_only:
            today = date.today()
            appointments = [apt for apt in appointments if apt.get("appointment_date") >= today.isoformat()]
        
        # 按日期排序
        appointments.sort(key=lambda x: x.get("appointment_date", ""))
        return [AppointmentModel(**apt) for apt in appointments]
    
    @staticmethod
    async def get_daily(target_date: date) -> dict:
        db = get_database()

        # 查询当日预约
        appointments = await db.get_appointments()
        target_date_str = target_date.isoformat()

        # 筛选当日预约（支持新旧格式）
        daily_appointments = []
        for apt in appointments:
            # 新格式：检查 start_time
            start_time = apt.get("start_time")
            if start_time:
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                if start_time.date() == target_date:
                    daily_appointments.append(apt)
                    continue

            # 旧格式：检查 appointment_date
            if apt.get("appointment_date") == target_date_str:
                daily_appointments.append(apt)

        # 按时间段分组
        slots = {}
        for apt in daily_appointments:
            # 获取时间段
            time_slot = None
            start_time = apt.get("start_time")

            if start_time:
                # 新格式：从 start_time 提取时间段
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                time_slot = start_time.strftime("%H:%M")
            else:
                # 旧格式：直接使用 time_slot
                time_slot = apt.get("time_slot", "")

            if time_slot not in slots:
                slots[time_slot] = []

            # 获取学员信息
            student = await db.get_student(apt.get("student_id"))
            if student:
                # 处理可能缺失的字段，设置默认值
                total_lessons = student.get("total_lessons", 0)
                remaining_lessons = student.get("remaining_lessons", total_lessons)  # 如果缺失，假设都是剩余课程
                attended_lessons = total_lessons - remaining_lessons

                # 计算动态状态
                status = apt.get("status", "scheduled")
                dynamic_status = status

                if start_time:
                    # 新格式：使用 start_time 和 end_time
                    end_time = apt.get("end_time")
                    if isinstance(end_time, str):
                        end_time = datetime.fromisoformat(end_time)
                    if end_time:
                        dynamic_status = calculate_dynamic_status_new(start_time, end_time, status)
                    else:
                        # 如果没有 end_time，默认1小时
                        end_time = start_time + timedelta(hours=1)
                        dynamic_status = calculate_dynamic_status_new(start_time, end_time, status)
                else:
                    # 旧格式：使用 appointment_date 和 time_slot
                    dynamic_status = calculate_dynamic_status(status, target_date, time_slot)

                slots[time_slot].append({
                    "id": apt.get("_id", ""),
                    "name": student.get("name", "未知学员"),
                    "package_type": student.get("package_type", "1v1"),
                    "learning_item": student.get("learning_item", "游泳"),
                    "attended_lessons": attended_lessons,
                    "total_lessons": total_lessons,
                    "appointment_id": apt.get("_id", ""),
                    "student_id": student.get("_id", ""),
                    "status": status,
                    "dynamic_status": dynamic_status
                })

        # 转换为列表格式
        slot_list = []
        for time_slot in sorted(slots.keys()):
            slot_list.append({
                "time": time_slot,
                "students": slots[time_slot]
            })

        # 获取星期
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday = weekdays[target_date.weekday()]

        return {
            "date": target_date.strftime("%m-%d"),
            "weekday": weekday,
            "is_past": target_date < date.today(),
            "slots": slot_list
        }

    @staticmethod
    async def get_upcoming(days: int = 30) -> List[dict]:
        from datetime import timedelta
        db = get_database()

        # 获取从今天开始的未来日期范围
        today = date.today()
        end_date = today + timedelta(days=days)

        # 查询所有预约
        appointments = await db.get_appointments()

        # 筛选未来预约（支持新旧格式）
        upcoming_appointments = []
        for apt in appointments:
            # 新格式：检查 start_time
            start_time = apt.get("start_time")
            if start_time:
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                apt_date = start_time.date()
                if today <= apt_date <= end_date:
                    upcoming_appointments.append(apt)
                    continue

            # 旧格式：检查 appointment_date
            appointment_date = apt.get("appointment_date")
            if appointment_date:
                try:
                    apt_date = date.fromisoformat(appointment_date)
                    if today <= apt_date <= end_date:
                        upcoming_appointments.append(apt)
                except ValueError:
                    continue

        # 按日期分组
        daily_groups = {}
        for apt in upcoming_appointments:
            # 确定日期
            start_time = apt.get("start_time")
            if start_time:
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time)
                day_date = start_time.date().isoformat()
            else:
                day_date = apt.get("appointment_date", "")

            if day_date not in daily_groups:
                daily_groups[day_date] = []
            daily_groups[day_date].append(apt)

        # 为每一天生成数据
        result = []
        for day_date in sorted(daily_groups.keys(), key=lambda x: date.fromisoformat(x)):
            day_appointments = daily_groups[day_date]
            date_obj = date.fromisoformat(day_date)

            # 按时间段分组
            slots = {}
            for apt in day_appointments:
                # 获取时间段
                time_slot = None
                start_time = apt.get("start_time")

                if start_time:
                    # 新格式：从 start_time 提取时间段
                    if isinstance(start_time, str):
                        start_time = datetime.fromisoformat(start_time)
                    time_slot = start_time.strftime("%H:%M")
                else:
                    # 旧格式：直接使用 time_slot
                    time_slot = apt.get("time_slot", "")

                if time_slot not in slots:
                    slots[time_slot] = []

                # 获取学员信息
                student = await db.get_student(apt.get("student_id"))
                if student:
                    # 处理可能缺失的字段，设置默认值
                    total_lessons = student.get("total_lessons", 0)
                    remaining_lessons = student.get("remaining_lessons", total_lessons)  # 如果缺失，假设都是剩余课程
                    attended_lessons = total_lessons - remaining_lessons

                    # 计算动态状态
                    status = apt.get("status", "scheduled")
                    dynamic_status = status

                    if start_time:
                        # 新格式：使用 start_time 和 end_time
                        end_time = apt.get("end_time")
                        if isinstance(end_time, str):
                            end_time = datetime.fromisoformat(end_time)
                        if end_time:
                            dynamic_status = calculate_dynamic_status_new(start_time, end_time, status)
                        else:
                            # 如果没有 end_time，默认1小时
                            end_time = start_time + timedelta(hours=1)
                            dynamic_status = calculate_dynamic_status_new(start_time, end_time, status)
                    else:
                        # 旧格式：使用 appointment_date 和 time_slot
                        dynamic_status = calculate_dynamic_status(status, date_obj, time_slot)

                    slots[time_slot].append({
                        "id": apt.get("_id", ""),
                        "name": student.get("name", "未知学员"),
                        "package_type": student.get("package_type", "1v1"),
                        "learning_item": student.get("learning_item", "游泳"),
                        "attended_lessons": attended_lessons,
                        "total_lessons": total_lessons,
                        "appointment_id": apt.get("_id", ""),
                        "student_id": student.get("_id", ""),
                        "status": status,
                        "dynamic_status": dynamic_status
                    })

            # 转换为列表格式
            slot_list = []
            for time_slot in sorted(slots.keys()):
                slot_list.append({
                    "time": time_slot,
                    "students": slots[time_slot]
                })

            # 获取星期
            weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            weekday = weekdays[date_obj.weekday()]

            result.append({
                "date": date_obj.strftime("%m-%d"),
                "weekday": weekday,
                "is_past": date_obj < today,
                "slots": slot_list
            })

        return result
    
    @staticmethod
    async def update(appointment_id: str, update_data: dict) -> Optional[AppointmentModel]:
        db = get_database()

        # 直接更新预约，不检查时间冲突
        success = await db.update_appointment(appointment_id, update_data)
        if success:
            updated = await db.get_appointment(appointment_id)
            if updated:
                return AppointmentModel(**updated)
        return None
    
    @staticmethod
    async def cancel(appointment_id: str) -> bool:
        db = get_database()

        # 获取预约信息
        appointment = await db.get_appointment(appointment_id)
        if not appointment:
            raise ValueError("预约不存在")

        # 获取学员信息
        student = await db.get_student(appointment.get("student_id"))
        if not student:
            raise ValueError("学员不存在")

        # 检查预约状态，只有scheduled状态的预约才能取消
        if appointment.get("status") != "scheduled":
            raise ValueError("只能取消待上课的预约")

        # 恢复课程次数
        current_remaining = student.get("remaining_lessons", 0)
        total_lessons = student.get("total_lessons", 0)

        # 确保不超过总课程数
        new_remaining = min(current_remaining + 1, total_lessons)

        # 更新学员剩余课程
        await db.update_student(appointment.get("student_id"), {
            "remaining_lessons": new_remaining,
            "update_time": datetime.utcnow()
        })

        # 更新预约状态为取消
        success = await db.update_appointment(appointment_id, {
            "status": "cancel",
            "update_time": datetime.utcnow()
        })

        return success

    @staticmethod
    async def delete(appointment_id: str) -> bool:
        db = get_database()
        return await db.delete_appointment(appointment_id)

class AttendanceService:
    @staticmethod
    async def checkin(appointment_id: str, student_id: str) -> AttendanceModel:
        db = get_database()

        # 获取学员和预约信息
        student = await db.get_student(student_id)
        appointment = await db.get_appointment(appointment_id)

        if not student:
            raise ValueError("学员不存在")
        if not appointment:
            raise ValueError("预约不存在")

        # 处理可能缺失的字段
        remaining_lessons = student.get("remaining_lessons", student.get("total_lessons", 0))
        if remaining_lessons <= 0:
            raise ValueError("剩余课程不足")
        if appointment.get("status") != "scheduled":
            raise ValueError("预约状态无效")

        # 检查是否已经签到
        attendances = await db.get_attendances()
        for att in attendances:
            if att.get("appointment_id") == appointment_id:
                raise ValueError("已经签到过了")

        # 获取时间信息（支持新旧格式）
        start_time = appointment.get("start_time")
        attendance_date = None
        time_slot = None

        if start_time:
            # 新格式：从 start_time 提取日期和时间
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            attendance_date = start_time.date()
            time_slot = start_time.strftime("%H:%M")
        else:
            # 旧格式：使用 appointment_date 和 time_slot
            appointment_date_str = appointment.get("appointment_date")
            if appointment_date_str:
                attendance_date = date.fromisoformat(appointment_date_str)
            time_slot = appointment.get("time_slot", "")

        # 创建上课记录
        attendance_data = {
            "student_id": student_id,
            "appointment_id": appointment_id,
            "attendance_date": attendance_date.isoformat() if attendance_date else "",
            "time_slot": time_slot,
            "status": "checked",
            "lessons_before": remaining_lessons,
            "lessons_after": remaining_lessons - 1,
            "create_time": datetime.utcnow()
        }

        # 插入上课记录
        await db.create_attendance(attendance_data)

        # 更新学员剩余课程
        await db.update_student(student_id, {"remaining_lessons": remaining_lessons - 1})

        # 更新预约状态
        await db.update_appointment(appointment_id, {"status": "checked", "update_time": datetime.utcnow()})

        attendance_data["_id"] = attendance_data.get("id", "")
        return AttendanceModel(**attendance_data)
    
    @staticmethod
    async def mark_cancel(appointment_id: str, student_id: str) -> AttendanceModel:
        db = get_database()

        # 获取预约信息
        appointment = await db.get_appointment(appointment_id)
        if not appointment:
            raise ValueError("预约不存在")

        # 获取学员信息
        student = await db.get_student(student_id)
        if not student:
            raise ValueError("学员不存在")

        # 处理可能缺失的字段
        remaining_lessons = student.get("remaining_lessons", student.get("total_lessons", 0))

        # 检查是否已经有考勤记录
        attendances = await db.get_attendances()
        for att in attendances:
            if att.get("appointment_id") == appointment_id and att.get("student_id") == student_id:
                raise ValueError("已经标记过考勤了")

        # 获取时间信息（支持新旧格式）
        start_time = appointment.get("start_time")
        attendance_date = None
        time_slot = None

        if start_time:
            # 新格式：从 start_time 提取日期和时间
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            attendance_date = start_time.date()
            time_slot = start_time.strftime("%H:%M")
        else:
            # 旧格式：使用 appointment_date 和 time_slot
            appointment_date_str = appointment.get("appointment_date")
            if appointment_date_str:
                attendance_date = date.fromisoformat(appointment_date_str)
            time_slot = appointment.get("time_slot", "")

        # 创建上课记录
        attendance_data = {
            "student_id": student_id,
            "appointment_id": appointment_id,
            "attendance_date": attendance_date.isoformat() if attendance_date else "",
            "time_slot": time_slot,
            "status": "cancel",
            "lessons_before": remaining_lessons,
            "lessons_after": remaining_lessons,
            "create_time": datetime.utcnow()
        }

        # 更新预约状态
        await db.update_appointment(appointment_id, {"status": "cancel", "update_time": datetime.utcnow()})

        # 插入考勤记录
        await db.create_attendance(attendance_data)

        attendance_data["_id"] = attendance_data.get("id", "")
        return AttendanceModel(**attendance_data)
    
    @staticmethod
    async def get_by_student(student_id: str) -> List[AttendanceModel]:
        db = get_database()
        attendances = await db.get_student_attendances(student_id)
        
        # 按日期排序
        attendances.sort(key=lambda x: x.get("attendance_date", ""), reverse=True)
        return [AttendanceModel(**att) for att in attendances]