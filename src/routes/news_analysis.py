"""
新闻分析服务路由
"""

from fastapi import APIRouter, Body

from src.config import config
from src.utils.proxy import proxy_request
from src.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger()


@router.post("/api/news-analysis")
async def analyze_news(text: str = Body(..., embed=True)) -> dict:
    """代理新闻分析请求，转发请求到新闻分析服务

    Args:
        text: 新闻文本内容

    Returns:
        dict: 新闻分析结果
    """
    return await proxy_request(
        service_url=config.get_service_url("news_analysis"),
        service_name="新闻分析",
        path="/api/analyze",
        method="POST",
        json_data={"text": text}
    )
