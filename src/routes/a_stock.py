"""
A股新股信息路由
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from src.config import config
from src.utils.proxy import proxy_request
from src.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger()


class AnalysisRequest(BaseModel):
    """分析请求模型"""
    text: str
    date: str | None = None


@router.get("/api/a-stock")
async def get_a_stock() -> dict:
    """代理 A股新股信息请求，转发请求到 A股后端服务

    Returns:
        dict: A股新股信息

    Raises:
        HTTPException: 服务未启用或不可用时
    """
    # 获取服务 URL
    service_url = config.get_service_url("a_stock")

    if not service_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="A股服务未启用或不可用"
        )

    return await proxy_request(
        service_url=service_url,
        service_name="A股",
        path="/api/stocks"
    )
