import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from typing import List, Dict, Optional
from datetime import datetime, date
from api_server.models import StudentModel, AppointmentModel, AttendanceModel

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
        """创建索引"""
        try:
            # 学生索引
            try:
                await self.db.students.create_index("name", unique=True)
            except:
                pass  # 索引可能已存在

            # 移除phone索引，改用可选字段
            try:
                await self.db.students.drop_index("phone")
                print("Phone index removed")
            except:
                pass  # 索引不存在
            
            # 预约索引
            try:
                await self.db.appointments.create_index([("student_id", ASCENDING), ("appointment_date", ASCENDING), ("time_slot", ASCENDING)], unique=True)
            except:
                pass  # 索引可能已存在
            
            try:
                await self.db.appointments.create_index("appointment_date")
            except:
                pass  # 索引可能已存在
            
            # 考勤索引
            try:
                await self.db.attendances.create_index([("student_id", ASCENDING), ("appointment_id", ASCENDING)], unique=True)
            except:
                pass  # 索引可能已存在
            
            try:
                await self.db.attendances.create_index("attendance_date")
            except:
                pass  # 索引可能已存在
            
            print("MongoDB indexes checked/created successfully")
        except Exception as e:
            print(f"Failed to create indexes: {e}")
    
    def _generate_id(self):
        """生成ObjectId字符串"""
        from bson import ObjectId
        return str(ObjectId())
    
    # 学生相关操作
    async def create_student(self, student_data: dict) -> str:
        """创建学生"""
        student_data["_id"] = self._generate_id()
        student_data["id"] = student_data["_id"]
        student_data["create_time"] = datetime.utcnow()
        student_data["update_time"] = datetime.utcnow()
        
        result = await self.db.students.insert_one(student_data)
        return str(result.inserted_id)
    
    async def get_student(self, student_id: str) -> Optional[dict]:
        """获取学生"""
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
        """获取所有学生"""
        if self.db is None:
            await self.connect()
        students = []
        async for student in self.db.students.find():
            student["_id"] = str(student["_id"])
            student["id"] = student["_id"]
            students.append(student)
        return students
    
    async def update_student(self, student_id: str, update_data: dict) -> bool:
        """更新学生"""
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
        """删除学生"""
        from bson import ObjectId
        try:
            # 删除学生
            result = await self.db.students.delete_one({"_id": ObjectId(student_id)})
        except:
            result = await self.db.students.delete_one({"_id": student_id})
        
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
        """获取学生的预约"""
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
        """获取学生的考勤记录"""
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