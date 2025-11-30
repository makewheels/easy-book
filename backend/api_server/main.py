from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api_server.database import connect_to_mongo, close_mongo_connection
from api_server.api import students, appointments, attendance
from dotenv import load_dotenv

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
app.include_router(appointments.router, prefix="/api/appointments", tags=["预约管理"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["签到管理"])

@app.get("/")
async def root():
    return {"message": "Easy Book API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    import sys
    port = 8002 if len(sys.argv) < 2 else int(sys.argv[1])
    uvicorn.run(app, host="0.0.0.0", port=port)