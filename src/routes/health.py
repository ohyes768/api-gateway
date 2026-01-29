"""
健康检查路由
"""

from datetime import datetime
from fastapi import APIRouter

from src.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger()


@router.get("/health")
async def health_check() -> dict:
    """Gateway 健康检查端点"""
    return {
        "status": "ok",
        "service": "api-gateway",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }
