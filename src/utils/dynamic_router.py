"""
动态路由注册器

根据配置文件动态注册路由到 FastAPI 应用
"""

from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse

import httpx

from src.config import config
from src.models.service_config import ServicesConfig
from src.utils.logger import setup_logger

logger = setup_logger()


class DynamicRouter:
    """动态路由注册器"""

    def __init__(self, app: FastAPI, services_config: ServicesConfig):
        """
        初始化动态路由注册器

        Args:
            app: FastAPI 应用实例
            services_config: 服务配置
        """
        self.app = app
        self.services_config = services_config
        # 缓存服务名称到 ServiceItem 的映射
        self._service_map: Dict[str, Any] = {}

    def register_all_routes(self):
        """注册所有配置的路由"""
        routes = self.services_config.get_all_routes()

        logger.info(f"开始动态注册路由，共 {len(routes)} 个路由")

        # 构建服务映射
        for service_name, service_item in self.services_config.services.items():
            self._service_map[service_name] = service_item

        # 为每个路由注册处理函数
        for service_name, path, method, backend_path in routes:
            self._register_route(service_name, path, method, backend_path)

        logger.info(f"✅ 路由注册完成")

    def _register_route(self, service_name: str, path: str, method: str, backend_path: str):
        """
        注册单个路由

        Args:
            service_name: 服务名称
            path: 网关路由路径
            method: HTTP 方法
            backend_path: 后端服务路径
        """

        async def route_handler(request: Request):
            """动态生成的路由处理函数"""
            service = self._service_map.get(service_name)

            if not service or not service.enabled:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"服务 {service_name} 未启用或不可用"
                )

            # 获取查询参数
            params = dict(request.query_params)

            # 获取请求体（对于 POST/PUT/PATCH）
            json_data = None
            if method.upper() in ["POST", "PUT", "PATCH"]:
                try:
                    json_data = await request.json()
                except Exception:
                    json_data = None

            # 转发请求
            return await self._proxy_request(
                service_url=service.url,
                service_name=service_name,
                backend_path=backend_path,
                method=method,
                params=params,
                json_data=json_data
            )

        # 注册路由到 FastAPI
        self.app.add_route(
            path=path,
            route=route_handler,
            methods=[method],
            name=f"{service_name}_{method}_{path.replace('/', '_')}"
        )

        logger.info(f"  ✓ 注册路由: {method:6} {path} -> {service_name}{backend_path}")

    async def _proxy_request(
        self,
        service_url: str,
        service_name: str,
        backend_path: str,
        method: str,
        params: dict = None,
        json_data: dict = None
    ) -> JSONResponse:
        """代理请求到后端服务

        Args:
            service_url: 后端服务地址
            service_name: 服务名称
            backend_path: 后端服务路径
            method: HTTP 方法
            params: URL 参数
            json_data: POST/PUT 请求的 JSON 数据

        Returns:
            JSONResponse: 代理的响应结果
        """
        try:
            url = f"{service_url}{backend_path}"
            logger.info(f"代理请求: {method} {url}")

            async with httpx.AsyncClient(timeout=config.TIMEOUT) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, json=json_data)
                elif method.upper() == "PUT":
                    response = await client.put(url, json=json_data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, params=params)
                elif method.upper() == "PATCH":
                    response = await client.patch(url, json=json_data)
                else:
                    raise HTTPException(status_code=400, detail=f"不支持的 HTTP 方法: {method}")

                logger.info(f"服务响应: {response.status_code}")

                try:
                    return JSONResponse(content=response.json(), status_code=response.status_code)
                except Exception:
                    # 如果响应不是 JSON，返回原始文本
                    return JSONResponse(content={"data": response.text}, status_code=response.status_code)

        except httpx.TimeoutException:
            logger.error(f"{service_name} 服务请求超时")
            raise HTTPException(status_code=503, detail=f"{service_name} 服务请求超时")

        except httpx.RequestError as e:
            logger.error(f"{service_name} 服务请求失败: {e}")
            raise HTTPException(status_code=503, detail=f"{service_name} 服务暂时不可用")

        except Exception as e:
            logger.error(f"未预期的错误: {e}")
            raise HTTPException(status_code=500, detail="内部服务错误")
