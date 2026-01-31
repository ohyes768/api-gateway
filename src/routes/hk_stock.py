"""
港股新股信息路由
"""

from fastapi import APIRouter, HTTPException, status

from src.config import config
from src.utils.proxy import proxy_request
from src.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger()


@router.get("/api/hk-stock")
async def get_hk_stock() -> dict:
    """代理港股新股信息请求，转发请求到港股后端服务

    Returns:
        dict: 港股新股信息

    Raises:
        HTTPException: 服务未启用或不可用时
    """
    # 获取服务 URL
    service_url = config.get_service_url("hk_stock")

    if not service_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="港股服务未启用或不可用"
        )

    return await proxy_request(
        service_url=service_url,
        service_name="港股",
        path="/api/stocks"
    )
