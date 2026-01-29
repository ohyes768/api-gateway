"""
港股新股信息路由
"""

from fastapi import APIRouter

from src.config import config
from src.utils.proxy import proxy_request
from src.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger()


@router.get("/api/hk-stock")
async def get_hk_stock() -> dict:
    """代理港股新股信息请求，转发请求到港股后端服务"""
    return await proxy_request(
        service_url=config.get_service_url("hk_stock"),
        service_name="港股",
        path="/api/stocks"
    )
