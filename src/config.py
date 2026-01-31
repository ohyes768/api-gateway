"""
API Gateway 配置管理
从 YAML 配置文件加载服务配置
"""

import os
import asyncio
from pathlib import Path
from typing import Optional

import yaml
import httpx

from src.models.service_config import ServicesConfig, ServiceItem


class Config:
    """应用配置类"""

    # 基础配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    TIMEOUT: int = int(os.getenv("TIMEOUT", "30"))

    # 服务配置
    APP_NAME: str = "API Gateway"
    VERSION: str = "2.1.0"
    services_config: ServicesConfig = None

    def __init__(self, config_path: str = "config/services.yaml"):
        """
        加载并验证配置

        Args:
            config_path: 配置文件路径

        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置格式错误或服务不可达
        """
        self._load_services_config(config_path)
        asyncio.run(self._validate_services_reachability())

    def _load_services_config(self, config_path: str):
        """加载服务配置文件"""
        # 如果是相对路径，则基于项目根目录（src 的父目录）
        config_file = Path(config_path)
        if not config_file.is_absolute():
            # 获取项目根目录（src/config.py 的父目录的父目录）
            project_root = Path(__file__).parent.parent
            config_file = project_root / config_path

        # 严格模式：配置文件必须存在
        if not config_file.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {config_path}\n"
                f"请创建配置文件并配置服务信息。"
            )

        # 解析 YAML
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 格式错误: {e}")

        # 验证配置格式
        try:
            self.services_config = ServicesConfig(**config_data)
        except Exception as e:
            raise ValueError(f"配置格式错误: {e}")

    async def _validate_services_reachability(self):
        """验证服务可达性（并发检查）"""
        async with httpx.AsyncClient(timeout=5.0) as client:
            tasks = []
            for name, service in self.services_config.services.items():
                if service.enabled:
                    tasks.append(self._check_service(client, name, service))

            if not tasks:
                # 没有启用的服务，跳过可达性检查
                return

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 检查是否有失败的服务
            for result in results:
                if isinstance(result, Exception):
                    raise ValueError(f"服务可达性检查失败: {result}")

    async def _check_service(
        self,
        client: httpx.AsyncClient,
        name: str,
        service: ServiceItem
    ):
        """检查单个服务的可达性"""
        health_url = f"{service.url}{service.health_path}"
        try:
            response = await client.get(health_url)
            if response.status_code != 200:
                raise ValueError(
                    f"服务 '{name}' 健康检查失败 "
                    f"({health_url}): {response.status_code}"
                )
        except httpx.RequestError as e:
            raise ValueError(
                f"服务 '{name}' 无法访问 "
                f"({health_url}): {e}"
            )

    def get_service_url(self, service_name: str) -> Optional[str]:
        """获取服务 URL

        Args:
            service_name: 服务名称（如 "news_analysis"）

        Returns:
            Optional[str]: 服务 URL，如果服务不存在或未启用则返回 None
        """
        service = self.services_config.services.get(service_name)
        if service and service.enabled:
            return service.url
        return None


# 全局配置实例
config = Config()
