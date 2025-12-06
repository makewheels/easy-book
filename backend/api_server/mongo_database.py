import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING
from bson import ObjectId
from typing import List, Dict, Optional
from datetime import datetime, date
from api_server.models import MongoDBStudentModel, MongoDBCourseModel, MongoDBAppointmentModel
from api_server.base_model import IndexManager

class MongoDatabase:
    def __init__(self):
        self.client = None
        self.db = None
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.db_name = os.getenv("DB_NAME", "easy_book")

    def _convert_id(self, doc: dict) -> dict:
        """将文档的_id字段转换为id字段"""
        if doc and "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
        return doc

    def _convert_objectid_to_string(self, doc: dict) -> dict:
        """将文档中的ObjectId字段转换为字符串，保持_id字段"""
        if doc and "_id" in doc:
            doc["_id"] = str(doc["_id"])
        return doc
    
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
            index_manager.register_model(MongoDBCourseModel)
            index_manager.register_model(MongoDBAppointmentModel)

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
        student_data["create_time"] = datetime.now()
        student_data["update_time"] = datetime.now()
        
        result = await self.db.students.insert_one(student_data)
        return str(result.inserted_id)
    
    async def get_student(self, student_id: str) -> Optional[dict]:
        """获取学员"""
        if self.db is None:
            await self.connect()

        # 首先尝试字符串查找，因为我们的ID是字符串格式
        student = await self.db.students.find_one({"_id": student_id})

        # 如果字符串查找失败，尝试ObjectId查找
        if not student:
            try:
                student = await self.db.students.find_one({"_id": ObjectId(student_id)})
            except:
                pass

        # 转换_id为id，供Python代码使用
        return self._convert_id(student) if student else None
    
    async def get_students(self) -> List[dict]:
        """获取所有学员"""
        if self.db is None:
            await self.connect()
        students = []
        async for student in self.db.students.find():
            # 转换_id为id，供Python代码使用
            students.append(self._convert_id(dict(student)))
        return students
    
    async def update_student(self, student_id: str, update_data: dict) -> bool:
        """更新学员"""
        from bson import ObjectId
        update_data["update_time"] = datetime.now()
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

        # 删除相关预约（使用新的 student_appointments 表）
        if result.deleted_count > 0:
            await self.db.student_appointments.delete_many({"student_id": student_id})

        return result.deleted_count > 0
    
  
    # 课程相关操作
    async def create_course(self, course_data: dict) -> str:
        """创建课程"""
        course_data["_id"] = self._generate_id()
        course_data["id"] = course_data["_id"]
        course_data["create_time"] = datetime.utcnow()
        course_data["update_time"] = datetime.utcnow()

        result = await self.db.courses.insert_one(course_data)
        return str(result.inserted_id)

    async def get_course(self, course_id: str) -> Optional[dict]:
        """获取课程信息"""
        course = await self.db.courses.find_one({"_id": course_id})
        return self._convert_id(course) if course else None

    async def update_course(self, course_id: str, update_data: dict) -> bool:
        """更新课程信息"""
        update_data["update_time"] = datetime.utcnow()
        result = await self.db.courses.update_one(
            {"_id": course_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def find_course_by_time(self, start_time: datetime, end_time: datetime) -> Optional[dict]:
        """根据开始和结束时间查找课程"""
        course = await self.db.courses.find_one({
            "start_time": start_time,
            "end_time": end_time,
            "status": "scheduled"
        })
        return self._convert_id(course) if course else None

    async def get_courses_by_date_range(self, start_date: datetime, end_date: datetime) -> List[dict]:
        """获取指定日期范围内的课程"""
        courses = []
        async for course in self.db.courses.find({
            "start_time": {"$gte": start_date, "$lt": end_date},
            "status": {"$ne": "cancelled"}
        }).sort("start_time", 1):
            courses.append(self._convert_id(dict(course)))
        return courses

    # 学生预约相关操作
    async def create_student_appointment(self, appointment_data: dict) -> str:
        """创建学生预约"""
        appointment_data["_id"] = self._generate_id()
        appointment_data["id"] = appointment_data["_id"]
        appointment_data["create_time"] = datetime.utcnow()
        appointment_data["update_time"] = datetime.utcnow()

        result = await self.db.student_appointments.insert_one(appointment_data)
        return str(result.inserted_id)

    async def get_student_appointments(self, student_id: str, status: Optional[str] = None) -> List[dict]:
        """获取学生的预约列表"""
        query = {"student_id": student_id}
        if status:
            query["status"] = status

        appointments = []
        async for appointment in self.db.student_appointments.find(query).sort("create_time", -1):
            appointments.append(self._convert_id(dict(appointment)))
        return appointments

    async def get_student_appointment(self, appointment_id: str) -> Optional[dict]:
        """根据ID获取单个学生预约"""
        appointment = await self.db.student_appointments.find_one({"_id": ObjectId(appointment_id)})
        return self._convert_id(appointment) if appointment else None

    async def get_course_appointments(self, course_id: str) -> List[dict]:
        """获取课程的所有预约"""
        appointments = []
        async for appointment in self.db.student_appointments.find({"course_id": course_id}).sort("create_time", 1):
            appointments.append(self._convert_id(dict(appointment)))
        return appointments

    async def update_student_appointment(self, appointment_id: str, update_data: dict) -> bool:
        """更新学生预约"""
        update_data["update_time"] = datetime.utcnow()
        result = await self.db.student_appointments.update_one(
            {"_id": appointment_id},
            {"$set": update_data}
        )
        return result.modified_count > 0

    async def delete_student_appointment(self, appointment_id: str) -> bool:
        """删除学生预约"""
        result = await self.db.student_appointments.delete_one({"_id": appointment_id})
        return result.deleted_count > 0

    async def check_student_time_conflict(self, student_id: str, start_time: datetime, end_time: datetime) -> bool:
        """检查学生时间冲突"""
        # 查找该学生在同一时间段的预约
        conflict = await self.db.student_appointments.find_one({
            "student_id": student_id,
            "status": "scheduled"
        })

        if conflict:
            # 获取关联的课程信息
            course = await self.get_course(conflict.get("course_id"))
            if course:
                # 检查时间是否重叠
                course_start = course.get("start_time")
                course_end = course.get("end_time")
                if isinstance(course_start, str):
                    course_start = datetime.fromisoformat(course_start)
                if isinstance(course_end, str):
                    course_end = datetime.fromisoformat(course_end)

                # 检查时间重叠
                if not (end_time <= course_start or start_time >= course_end):
                    return True
        return False


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