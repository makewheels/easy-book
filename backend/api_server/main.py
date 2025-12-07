from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from api_server.database import connect_to_mongo, close_mongo_connection
from api_server.api import students, courses, appointments, packages
from dotenv import load_dotenv
import json
import os

# 加载环境变量
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(
    title="Easy Book - 泳课学员管理系统",
    description="轻量级泳课学员管理系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置JSON响应器，直接返回中文字符而不使用Unicode转义
class PrettyJSONResponse(JSONResponse):
    def render(self, content) -> str:
        return json.dumps(
            content,
            ensure_ascii=False,  # 不使用ASCII转义，直接返回中文字符
            separators=(",", ":"),  # 紧凑格式，去除空格
            default=str  # 处理不能直接序列化的对象
        )

# 设置默认响应器
app.default_response_class = PrettyJSONResponse

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(students.router, prefix="/api/students", tags=["学员管理"])
app.include_router(courses.router, prefix="/api/courses", tags=["课程管理"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["预约管理"])
app.include_router(packages.router, prefix="/api/packages", tags=["套餐管理"])

@app.get("/")
async def root():
    return {"message": "Easy Book API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/health/db")
async def db_health_check():
    try:
        from api_server.database import test_connection
        db_status = await test_connection()
        return {"database": "healthy", "connection": db_status}
    except Exception as e:
        return {"database": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    import sys
    port = 8002 if len(sys.argv) < 2 else int(sys.argv[1])
    uvicorn.run(app, host="0.0.0.0", port=port)