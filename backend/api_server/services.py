from typing import List, Optional
from datetime import datetime, date, timedelta
from api_server.models import StudentModel, AppointmentModel, AttendanceModel
from api_server.database import get_database

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
        """为学生数据提供默认值"""
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

        # 处理日期格式（确保统一存储为字符串）
        appointment_date = appointment_data["appointment_date"]
        if isinstance(appointment_date, date):
            appointment_data["appointment_date"] = appointment_date.isoformat()

        # 直接创建预约，不检查时间冲突
        appointment_id = await db.create_appointment(appointment_data)
        appointment_data["_id"] = appointment_id
        appointment_data["id"] = appointment_id

        return AppointmentModel(**appointment_data)
    
    @staticmethod
    async def check_conflict(student_id: str, appointment_date, time_slot: str):
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
        
        # 检查同一个学生是否已经在同一时间预约
        appointments = await db.get_appointments()
        for apt in appointments:
            if (apt.get("appointment_date") == appointment_date_obj.isoformat() and
                apt.get("time_slot") == time_slot and
                apt.get("status") != "cancelled"):
                
                # 如果是同一个学生，直接报错
                if apt.get("student_id") == student_id:
                    raise ValueError(f"您已经在 {time_slot} 预约了课程")
                
                # 如果是1v1课程，检查与其他学生的冲突
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
        
        daily_appointments = [apt for apt in appointments if apt.get("appointment_date") == target_date_str]
        
        # 按时间段分组
        slots = {}
        for apt in daily_appointments:
            time_slot = apt["time_slot"]
            if time_slot not in slots:
                slots[time_slot] = []
            
            # 获取学员信息
            student = await db.get_student(apt.get("student_id"))
            if student:
                # 处理可能缺失的字段，设置默认值
                total_lessons = student.get("total_lessons", 0)
                remaining_lessons = student.get("remaining_lessons", total_lessons)  # 如果缺失，假设都是剩余课程
                attended_lessons = total_lessons - remaining_lessons

                slots[time_slot].append({
                    "id": apt.get("_id", ""),
                    "name": student.get("name", "未知学员"),
                    "package_type": student.get("package_type", "1v1"),
                    "learning_item": student.get("learning_item", "游泳"),
                    "attended_lessons": attended_lessons,
                    "total_lessons": total_lessons,
                    "appointment_id": apt.get("_id", ""),
                    "student_id": student.get("_id", ""),
                    "status": apt.get("status", "scheduled")
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

        # 筛选未来预约
        upcoming_appointments = []
        for apt in appointments:
            apt_date = date.fromisoformat(apt.get("appointment_date"))
            if today <= apt_date <= end_date:
                upcoming_appointments.append(apt)

        # 按日期分组
        daily_groups = {}
        for apt in upcoming_appointments:
            apt_date = apt.get("appointment_date")
            if apt_date not in daily_groups:
                daily_groups[apt_date] = []
            daily_groups[apt_date].append(apt)

        # 为每一天生成数据
        result = []
        for day_date in sorted(daily_groups.keys()):
            day_appointments = daily_groups[day_date]
            date_obj = date.fromisoformat(day_date)

            # 按时间段分组
            slots = {}
            for apt in day_appointments:
                time_slot = apt["time_slot"]
                if time_slot not in slots:
                    slots[time_slot] = []

                # 获取学员信息
                student = await db.get_student(apt.get("student_id"))
                if student:
                    # 处理可能缺失的字段，设置默认值
                    total_lessons = student.get("total_lessons", 0)
                    remaining_lessons = student.get("remaining_lessons", total_lessons)  # 如果缺失，假设都是剩余课程
                    attended_lessons = total_lessons - remaining_lessons

                    slots[time_slot].append({
                        "id": apt.get("_id", ""),
                        "name": student.get("name", "未知学员"),
                        "package_type": student.get("package_type", "1v1"),
                        "learning_item": student.get("learning_item", "游泳"),
                        "attended_lessons": attended_lessons,
                        "total_lessons": total_lessons,
                        "appointment_id": apt.get("_id", ""),
                        "student_id": student.get("_id", ""),
                        "status": apt.get("status", "scheduled")
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
        
        # 创建上课记录
        attendance_data = {
            "student_id": student_id,
            "appointment_id": appointment_id,
            "attendance_date": appointment.get("appointment_date"),
            "time_slot": appointment.get("time_slot"),
            "status": "checked",
            "lessons_before": remaining_lessons,
            "lessons_after": remaining_lessons - 1,
        }
        
        # 插入上课记录
        await db.create_attendance(attendance_data)
        
        # 更新学员剩余课程
        await db.update_student(student_id, {"remaining_lessons": student["remaining_lessons"] - 1})
        
        # 更新预约状态
        await db.update_appointment(appointment_id, {"status": "checked"})
        
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

        # 创建上课记录
        attendance_data = {
            "student_id": student_id,
            "appointment_id": appointment_id,
            "attendance_date": appointment.get("appointment_date"),
            "time_slot": appointment.get("time_slot"),
            "status": "cancel",
            "lessons_before": remaining_lessons,
            "lessons_after": remaining_lessons,
        }
        
        # 更新预约状态
        await db.update_appointment(appointment_id, {"status": "cancel"})
        
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