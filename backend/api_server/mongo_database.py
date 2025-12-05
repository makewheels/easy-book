import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from typing import List, Dict, Optional
from datetime import datetime, date
from api_server.models import MongoDBStudentModel, MongoDBAppointmentModel, MongoDBAttendanceModel
from api_server.base_model import IndexManager

class MongoDatabase:
    def __init__(self):
        self.client = None
        self.db = None
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.db_name = os.getenv("DB_NAME", "easy_book")
    
    async def connect(self):
        """连接到MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.db = self.client[self.db_name]
            await self.client.admin.command('ping')
            print(f"Connected to MongoDB at {self.mongodb_url}")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """断开MongoDB连接"""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")
    
    async def create_indexes(self):
        """使用模型系统创建索引"""
        try:
            # 创建索引管理器
            index_manager = IndexManager(self.db)

            # 注册所有模型
            index_manager.register_model(MongoDBStudentModel)
            index_manager.register_model(MongoDBAppointmentModel)
            index_manager.register_model(MongoDBAttendanceModel)

            # 创建所有索引
            success = index_manager.create_all_indexes()

            if success:
                print("所有模型索引创建完成 (遵循项目规范：不使用唯一约束)")
            else:
                print("部分索引创建失败，请检查日志")

        except Exception as e:
            print(f"索引创建过程中发生错误: {e}")
    
    def _generate_id(self):
        """生成ObjectId字符串"""
        from bson import ObjectId
        return str(ObjectId())
    
    # 学员相关操作
    async def create_student(self, student_data: dict) -> str:
        """创建学员"""
        student_data["_id"] = self._generate_id()
        student_data["id"] = student_data["_id"]
        student_data["create_time"] = datetime.utcnow()
        student_data["update_time"] = datetime.utcnow()
        
        result = await self.db.students.insert_one(student_data)
        return str(result.inserted_id)
    
    async def get_student(self, student_id: str) -> Optional[dict]:
        """获取学员"""
        if self.db is None:
            await self.connect()
        from bson import ObjectId
        # 首先尝试字符串查找，因为我们的ID是字符串格式
        student = await self.db.students.find_one({"_id": student_id})
        
        # 如果字符串查找失败，尝试ObjectId查找
        if not student:
            try:
                student = await self.db.students.find_one({"_id": ObjectId(student_id)})
            except:
                pass
        
        if student:
            student["_id"] = str(student["_id"])
            student["id"] = student["_id"]
        return student
    
    async def get_students(self) -> List[dict]:
        """获取所有学员"""
        if self.db is None:
            await self.connect()
        students = []
        async for student in self.db.students.find():
            student["_id"] = str(student["_id"])
            student["id"] = student["_id"]
            students.append(student)
        return students
    
    async def update_student(self, student_id: str, update_data: dict) -> bool:
        """更新学员"""
        from bson import ObjectId
        update_data["update_time"] = datetime.utcnow()
        # 首先尝试字符串查找，因为我们的ID是字符串格式
        result = await self.db.students.update_one(
            {"_id": student_id},
            {"$set": update_data}
        )
        # 如果字符串查找失败，尝试ObjectId查找
        if result.modified_count == 0:
            try:
                result = await self.db.students.update_one(
                    {"_id": ObjectId(student_id)},
                    {"$set": update_data}
                )
            except:
                pass
        return result.modified_count > 0
    
    async def delete_student(self, student_id: str) -> bool:
        """删除学员"""
        from bson import ObjectId
        # 首先尝试字符串查找，与get_student保持一致
        result = await self.db.students.delete_one({"_id": student_id})

        # 如果字符串查找失败，尝试ObjectId查找
        if result.deleted_count == 0:
            try:
                result = await self.db.students.delete_one({"_id": ObjectId(student_id)})
            except:
                pass

        # 删除相关预约和考勤
        if result.deleted_count > 0:
            await self.db.appointments.delete_many({"student_id": student_id})
            await self.db.attendances.delete_many({"student_id": student_id})

        return result.deleted_count > 0
    
    # 预约相关操作
    async def create_appointment(self, appointment_data: dict) -> str:
        """创建预约"""
        if self.db is None:
            await self.connect()
        appointment_data["_id"] = self._generate_id()
        appointment_data["id"] = appointment_data["_id"]
        appointment_data["create_time"] = datetime.utcnow()
        appointment_data["update_time"] = datetime.utcnow()
        appointment_data["status"] = "scheduled"
        
        result = await self.db.appointments.insert_one(appointment_data)
        return str(result.inserted_id)
    
    async def get_appointment(self, appointment_id: str) -> Optional[dict]:
        """获取预约"""
        from bson import ObjectId
        # 首先尝试字符串查找，因为我们的ID是字符串格式
        appointment = await self.db.appointments.find_one({"_id": appointment_id})
        
        # 如果字符串查找失败，尝试ObjectId查找
        if not appointment:
            try:
                appointment = await self.db.appointments.find_one({"_id": ObjectId(appointment_id)})
            except:
                pass
        
        if appointment:
            appointment["_id"] = str(appointment["_id"])
            appointment["id"] = appointment["_id"]
        return appointment
    
    async def get_appointments(self) -> List[dict]:
        """获取所有预约"""
        if self.db is None:
            await self.connect()
        appointments = []
        async for appointment in self.db.appointments.find():
            appointment["_id"] = str(appointment["_id"])
            appointment["id"] = appointment["_id"]
            appointments.append(appointment)
        return appointments
    
    async def get_student_appointments(self, student_id: str) -> List[dict]:
        """获取学员的预约"""
        appointments = []
        async for appointment in self.db.appointments.find({"student_id": student_id}):
            appointment["_id"] = str(appointment["_id"])
            appointment["id"] = appointment["_id"]
            appointments.append(appointment)
        return appointments
    
    async def update_appointment(self, appointment_id: str, update_data: dict) -> bool:
        """更新预约"""
        from bson import ObjectId
        update_data["update_time"] = datetime.utcnow()
        # 首先尝试字符串查找，与get_appointment保持一致
        result = await self.db.appointments.update_one(
            {"_id": appointment_id}, 
            {"$set": update_data}
        )
        
        # 如果字符串查找没有更新任何记录，尝试ObjectId查找
        if result.modified_count == 0:
            try:
                result = await self.db.appointments.update_one(
                    {"_id": ObjectId(appointment_id)}, 
                    {"$set": update_data}
                )
            except:
                pass
        return result.modified_count > 0
    
    async def delete_appointment(self, appointment_id: str) -> bool:
        """删除预约"""
        from bson import ObjectId
        try:
            # 删除预约
            result = await self.db.appointments.delete_one({"_id": ObjectId(appointment_id)})
        except:
            result = await self.db.appointments.delete_one({"_id": appointment_id})

        # 删除相关考勤
        if result.deleted_count > 0:
            await self.db.attendances.delete_many({"appointment_id": appointment_id})

        return result.deleted_count > 0

    async def get_daily_appointments(self, appointment_date: str) -> dict:
        """获取指定日期的预约数据"""
        if self.db is None:
            await self.connect()

        # 获取指定日期的所有预约（包括已取消的预约，但会显示状态）
        appointments = []
        async for appointment in self.db.appointments.find({
            "appointment_date": appointment_date
        }):
            appointment["_id"] = str(appointment["_id"])
            appointment["id"] = appointment["_id"]
            appointments.append(appointment)

        # 按时间段组织数据
        time_slots = {}

        # 只包含有预约的时间段
        for appointment in appointments:
            time_slot = None

            # 尝试从新格式获取时间
            if "start_time" in appointment:
                from datetime import datetime
                try:
                    start_dt = datetime.fromisoformat(appointment["start_time"].replace('Z', '+00:00'))
                    time_slot = start_dt.strftime("%H:%M")
                except:
                    pass

            # 如果新格式失败，尝试从旧格式获取
            if not time_slot and "time_slot" in appointment:
                time_slot = appointment["time_slot"]

            if time_slot:
                if time_slot not in time_slots:
                    time_slots[time_slot] = []

                # 查询学生详细信息
                student_name = ""
                student_info = None
                if appointment.get("student_id"):
                    student_info = await self.get_student(appointment["student_id"])
                    if student_info:
                        student_name = student_info.get("name", "")

                # 添加学生信息
                student_data = {
                    "id": appointment["_id"],
                    "name": student_name,
                    "package_type": appointment.get("package_type", ""),
                    "learning_item": appointment.get("learning_item", ""),
                    "appointment_id": appointment["_id"],
                    "student_id": appointment.get("student_id", ""),
                    "status": appointment.get("status", "scheduled"),
                    "dynamic_status": appointment.get("status", "scheduled")
                }

                # 补充学生统计信息
                if student_info:
                    student_data["total_lessons"] = student_info.get("total_lessons", 0)
                    student_data["attended_lessons"] = student_info.get("attended_lessons", 0)

                time_slots[time_slot].append(student_data)

        # 构建返回数据
        result = {
            "date": appointment_date,
            "weekday": self._get_weekday(appointment_date),
            "is_past": self._is_past_date(appointment_date),
            "slots": []
        }

        # 只添加有学生的时间段
        for time_slot in sorted(time_slots.keys()):
            if time_slots[time_slot]:  # 只有当这个时段有学生时才添加
                result["slots"].append({
                    "time": time_slot,
                    "students": time_slots[time_slot]
                })

        return result

    async def get_upcoming_appointments(self, days: int = 30) -> List[dict]:
        """获取从今天开始到未来指定天数的预约数据"""
        if self.db is None:
            await self.connect()

        from datetime import datetime, timedelta

        # 生成日期列表
        today = datetime.now()
        date_list = []
        for i in range(days):
            date = today + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            date_list.append(date_str)

        # 获取所有日期的预约数据
        upcoming_data = []
        for date_str in date_list:
            daily_data = await self.get_daily_appointments(date_str)
            if daily_data and daily_data.get("slots"):
                upcoming_data.append(daily_data)

        return upcoming_data

    def _get_weekday(self, date_str: str) -> str:
        """获取星期几"""
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            weekdays = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"]
            return weekdays[date_obj.weekday()]
        except:
            return ""

    def _is_past_date(self, date_str: str) -> bool:
        """判断日期是否已过"""
        try:
            from datetime import datetime
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return date_obj < today
        except:
            return False
    
    async def check_appointment_conflict(self, student_id: str, appointment_date: str, time_slot: str) -> bool:
        """检查预约冲突"""
        conflict = await self.db.appointments.find_one({
            "student_id": student_id,
            "appointment_date": appointment_date,
            "time_slot": time_slot,
            "status": {"$ne": "cancelled"}
        })
        return conflict is not None
    
    # 考勤相关操作
    async def create_attendance(self, attendance_data: dict) -> str:
        """创建考勤记录"""
        attendance_data["_id"] = self._generate_id()
        attendance_data["id"] = attendance_data["_id"]
        attendance_data["create_time"] = datetime.utcnow()
        
        result = await self.db.attendances.insert_one(attendance_data)
        return str(result.inserted_id)
    
    async def get_attendances(self) -> List[dict]:
        """获取所有考勤记录"""
        attendances = []
        async for attendance in self.db.attendances.find():
            attendance["_id"] = str(attendance["_id"])
            attendance["id"] = attendance["_id"]
            attendances.append(attendance)
        return attendances
    
    async def get_student_attendances(self, student_id: str) -> List[dict]:
        """获取学员的考勤记录"""
        attendances = []
        async for attendance in self.db.attendances.find({"student_id": student_id}):
            attendance["_id"] = str(attendance["_id"])
            attendance["id"] = attendance["_id"]
            attendances.append(attendance)
        return attendances

# 全局数据库实例
db = MongoDatabase()

# 数据库访问函数
async def connect_to_mongo():
    """连接数据库"""
    await db.connect()
    await db.create_indexes()

async def close_mongo_connection():
    """关闭数据库连接"""
    await db.disconnect()

async def create_indexes():
    """创建索引"""
    await db.create_indexes()

def get_database():
    """获取数据库实例"""
    return db

async def test_connection():
    """测试数据库连接"""
    try:
        if db.client is None:
            await db.connect()
        
        # 执行简单的ping测试
        await db.client.admin.command('ping')
        
        # 测试数据库访问
        await db.db.command('ping')
        
        return "connected"
    except Exception as e:
        return f"error: {str(e)}"