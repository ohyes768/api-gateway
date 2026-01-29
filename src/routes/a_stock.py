"""
A股新股信息路由
"""

from fastapi import APIRouter
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
    """代理 A股新股信息请求，转发请求到 A股后端服务"""
    return await proxy_request(
        service_url=config.get_service_url("a_stock"),
        service_name="A股",
        path="/api/stocks"
    )
