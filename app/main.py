from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routers import clipboard
from app.database import init_db
import asyncio

app = FastAPI(
    title="Shared Clipboard API",
    description="A real-time shared clipboard service",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 包含路由
app.include_router(clipboard.router)

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库"""
    await init_db()

@app.get("/")
async def root():
    return FileResponse("app/static/index.html")