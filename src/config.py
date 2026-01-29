"""
API Gateway 配置管理

从环境变量加载配置
"""

import os
from typing import Dict, Optional


class Config:
    """应用配置类"""

    # 基础配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    TIMEOUT: int = int(os.getenv("TIMEOUT", "30"))

    # 服务配置
    APP_NAME: str = "通用 API Gateway"
    VERSION: str = "2.0.0"

    # 后端服务注册（可扩展）
    SERVICES: Dict[str, str] = {
        "a_stock": os.getenv("A_STOCK_SERVICE_URL", "http://a-stock-service:8001"),
        "hk_stock": os.getenv("HK_STOCK_SERVICE_URL", "http://hk-stock-service:8002"),
        "news_analysis": os.getenv("NEWS_ANALYSIS_SERVICE_URL", "http://news-analysis-service:8030"),
    }

    @classmethod
    def get_service_url(cls, service_name: str) -> Optional[str]:
        """获取服务 URL

        Args:
            service_name: 服务名称（如 "a_stock", "hk_stock", "news_analysis"）

        Returns:
            Optional[str]: 服务 URL，如果服务不存在则返回 None
        """
        return cls.SERVICES.get(service_name)


# 全局配置实例
config = Config()
