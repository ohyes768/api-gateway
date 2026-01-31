"""
API Gateway - FastAPI 主入口

通用 API 网关，提供统一入口，根据配置动态路由转发到后端微服务
"""

import os
from typing import Final

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config import config
from src.routes import health
from src.utils.dynamic_router import DynamicRouter
from src.utils.logger import setup_logger

# 常量定义
DEFAULT_PORT: Final = 8000

# 创建 FastAPI 应用
app = FastAPI(
    title=config.APP_NAME,
    version=config.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 初始化日志
logger = setup_logger(level=config.LOG_LEVEL)


# 注册健康检查路由（保留，因为不需要动态配置）
app.include_router(health.router, tags=["健康检查"])


# 全局异常处理器
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc) -> JSONResponse:
    """HTTP 异常处理器"""
    logger.error(f"HTTP 异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc) -> JSONResponse:
    """请求验证异常处理器"""
    logger.error(f"请求验证失败: {exc}")
    return JSONResponse(
        status_code=422,
        content={"error": "请求参数验证失败", "details": exc.errors()}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc) -> JSONResponse:
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "内部服务错误"}
    )


# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info(f"🚀 {config.APP_NAME} v{config.VERSION} 启动中...")

    # 动态注册所有路由
    dynamic_router = DynamicRouter(app, config.services_config)
    dynamic_router.register_all_routes()

    # 记录已注册的服务
    enabled_services = config.services_config.get_enabled_services()
    logger.info(f"📋 已注册服务: {list(enabled_services.keys())}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info(f"👋 {config.APP_NAME} 已停止")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", str(DEFAULT_PORT)))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level=config.LOG_LEVEL.lower(),
        access_log=True,
        reload=False
    )
