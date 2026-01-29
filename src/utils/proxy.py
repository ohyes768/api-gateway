"""
代理工具

封装通用的代理请求逻辑
"""

import httpx
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from src.config import config
from src.utils.logger import setup_logger

logger = setup_logger()


async def proxy_request(
    service_url: str,
    service_name: str,
    path: str = "/",
    method: str = "GET",
    params: dict = None,
    json_data: dict = None
) -> JSONResponse:
    """代理请求到后端服务

    Args:
        service_url: 后端服务地址
        service_name: 服务名称（用于日志）
        path: 请求路径
        method: HTTP 方法（GET, POST, PUT, DELETE）
        params: URL 参数
        json_data: POST 请求的 JSON 数据

    Returns:
        JSONResponse: 代理的响应结果

    Raises:
        HTTPException: 当服务请求失败时
    """
    try:
        logger.info(f"收到 {service_name} 服务请求: {method} {service_url}{path}")

        async with httpx.AsyncClient(timeout=config.TIMEOUT) as client:
            if method.upper() == "GET":
                response = await client.get(f"{service_url}{path}", params=params)
            elif method.upper() == "POST":
                response = await client.post(f"{service_url}{path}", json=json_data)
            elif method.upper() == "PUT":
                response = await client.put(f"{service_url}{path}", json=json_data)
            elif method.upper() == "DELETE":
                response = await client.delete(f"{service_url}{path}")
            else:
                raise HTTPException(status_code=400, detail=f"不支持的 HTTP 方法: {method}")

            logger.info(f"{service_name} 服务响应状态码: {response.status_code}")

            try:
                return JSONResponse(content=response.json(), status_code=response.status_code)
            except Exception:
                # 如果响应不是 JSON，返回原始文本
                return JSONResponse(content={"data": response.text}, status_code=response.status_code)

    except httpx.TimeoutException:
        logger.error(f"{service_name} 服务请求超时")
        raise HTTPException(status_code=503, detail=f"{service_name}服务请求超时")

    except httpx.RequestError as e:
        logger.error(f"{service_name} 服务请求失败: {e}")
        raise HTTPException(status_code=503, detail=f"{service_name}服务暂时不可用")

    except Exception as e:
        logger.error(f"未预期的错误: {e}")
        raise HTTPException(status_code=500, detail="内部服务错误")
