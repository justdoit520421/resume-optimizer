# FastAPI 应用入口：注册路由、中间件、异常处理器
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.exceptions import BizException
from app.response import BizCode, Response
from app.api import resume

app = FastAPI(title="简历智能优化工具", version="0.1.0")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(resume.router, prefix="/api/resumes", tags=["简历"])


@app.on_event("startup")
def on_startup():
    """启动时建表"""
    init_db()


@app.get("/api/health")
def health():
    return Response.ok({"status": "ok"})


# ---------- 全局异常处理器 ----------
@app.exception_handler(BizException)
async def biz_exception_handler(request: Request, exc: BizException):
    return JSONResponse(
        status_code=200,
        content=Response.fail(exc.code, exc.message).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=200,
        content=Response.fail(BizCode.PARAM_ERROR, f"参数校验失败: {exc.errors()[0].get('msg')}").model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content=Response.fail(BizCode.INTERNAL_ERROR, f"服务器内部错误: {str(exc)}").model_dump(),
    )
