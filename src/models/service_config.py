"""
服务配置数据模型
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional, Literal
from urllib.parse import urlparse


class RouteItem(BaseModel):
    """路由配置项"""

    path: str = Field(..., description="网关路由路径（客户端访问的路径）")
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(
        default="GET",
        description="HTTP 方法"
    )
    backend_path: Optional[str] = Field(
        default=None,
        description="后端服务路径，默认与 path 相同"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "path": "/api/news-analysis",
                "method": "POST",
                "backend_path": "/api/analyze"
            }
        }
    }

    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """验证路径格式"""
        if not v.startswith('/'):
            raise ValueError('path must start with /')
        return v

    @field_validator('backend_path')
    @classmethod
    def validate_backend_path(cls, v: Optional[str]) -> Optional[str]:
        """验证后端路径格式"""
        if v is not None and not v.startswith('/'):
            raise ValueError('backend_path must start with /')
        return v


class ServiceItem(BaseModel):
    """单个服务配置"""

    url: str = Field(..., description="服务 URL")
    enabled: bool = Field(default=True, description="是否启用")
    health_path: str = Field(
        default="/health",
        description="健康检查路径"
    )
    routes: List[RouteItem] = Field(
        default_factory=list,
        description="路由配置列表"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "http://news-analysis-service:8030",
                "enabled": True,
                "health_path": "/health",
                "routes": [
                    {
                        "path": "/api/news-analysis",
                        "method": "POST",
                        "backend_path": "/api/analyze"
                    }
                ]
            }
        }
    }

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """验证 URL 格式"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')

        # 检查是否包含主机
        parsed = urlparse(v)
        if not parsed.netloc:
            raise ValueError('Invalid URL format')

        return v

    @field_validator('health_path')
    @classmethod
    def validate_health_path(cls, v: str) -> str:
        """验证健康检查路径"""
        if not v.startswith('/'):
            raise ValueError('health_path must start with /')
        return v

    @field_validator('routes')
    @classmethod
    def validate_routes_not_empty(cls, v: List[RouteItem]) -> List[RouteItem]:
        """如果服务启用，必须至少配置一个路由"""
        # 注意：这里不能访问 self.enabled，所以只在有路由时验证
        for route in v:
            if not route.path.startswith('/'):
                raise ValueError('route path must start with /')
        return v


class ServicesConfig(BaseModel):
    """服务配置集合"""

    services: Dict[str, ServiceItem] = Field(
        ...,
        description="服务配置字典，key 为服务名称"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "services": {
                    "news_analysis": {
                        "url": "http://news-analysis-service:8030",
                        "enabled": True,
                        "health_path": "/health",
                        "routes": [
                            {
                                "path": "/api/news-analysis",
                                "method": "POST",
                                "backend_path": "/api/analyze"
                            }
                        ]
                    },
                    "a_stock": {
                        "url": "http://a-stock-service:8001",
                        "enabled": True,
                        "routes": [
                            {
                                "path": "/api/a-stock",
                                "method": "GET",
                                "backend_path": "/api/stocks"
                            }
                        ]
                    }
                }
            }
        }
    }

    @field_validator('services')
    @classmethod
    def validate_services_not_empty(cls, v: Dict[str, ServiceItem]) -> Dict[str, ServiceItem]:
        """至少配置一个服务"""
        if not v or len(v) == 0:
            raise ValueError('At least one service must be configured')
        return v

    def get_enabled_services(self) -> Dict[str, ServiceItem]:
        """获取所有启用的服务"""
        return {
            name: service
            for name, service in self.services.items()
            if service.enabled
        }

    def get_all_routes(self) -> List[tuple[str, str, str, str]]:
        """
        获取所有路由配置

        Returns:
            List[tuple]: [(service_name, path, method, backend_path), ...]
        """
        routes = []
        for service_name, service in self.services.items():
            if service.enabled:
                for route in service.routes:
                    backend_path = route.backend_path or route.path
                    routes.append((service_name, route.path, route.method, backend_path))
        return routes
