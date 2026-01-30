# 开发指南

## 目录

- [开发环境搭建](#开发环境搭建)
- [项目结构](#项目结构)
- [代码规范](#代码规范)
- [开发流程](#开发流程)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)
- [添加新服务路由](#添加新服务路由)
- [常见开发任务](#常见开发任务)

---

## 开发环境搭建

### 前置要求

- **Python**: 3.10+
- **uv**: Python 包管理器
- **Git**: 版本控制
- **IDE**: VS Code / PyCharm / 其他

### 安装步骤

#### 1. 克隆仓库

```bash
git clone <repository-url>
cd api-gateway
```

#### 2. 安装 uv

**Windows (PowerShell)**:
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux / macOS**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### 3. 创建虚拟环境

```bash
uv venv .venv
```

#### 4. 激活虚拟环境

**Windows**:
```bash
.venv\Scripts\activate
```

**Linux / macOS**:
```bash
source .venv/bin/activate
```

#### 5. 安装依赖

```bash
uv pip install -r requirements.txt
```

#### 6. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置本地后端服务地址。

#### 7. 启动开发服务器

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8010 --reload
```

访问 `http://localhost:8010` 验证服务是否正常运行。

---

## 项目结构

```
api-gateway/
├── src/                    # 源代码目录
│   ├── __init__.py         # 包初始化
│   ├── main.py             # FastAPI 应用入口
│   ├── config.py           # 配置管理
│   ├── routes/             # 路由模块
│   │   ├── __init__.py
│   │   ├── health.py       # 健康检查路由
│   │   ├── a_stock.py      # A股新股信息路由
│   │   ├── hk_stock.py     # 港股新股信息路由
│   │   └── news_analysis.py # 新闻分析路由
│   └── utils/              # 工具模块
│       ├── __init__.py
│       ├── logger.py       # 日志工具
│       └── proxy.py        # 代理工具
├── tests/                  # 测试目录
├── docs/                   # 文档目录
├── scripts/                # 运行脚本目录
├── .env.example            # 环境变量示例
├── .gitignore              # Git 忽略规则
├── Dockerfile              # Docker 镜像配置
├── docker-compose.yml      # Docker Compose 配置
├── requirements.txt        # Python 依赖列表
└── README.md               # 项目说明
```

### 核心模块说明

#### main.py - 应用入口

FastAPI 应用的主入口文件，负责：
- 初始化 FastAPI 应用
- 注册所有路由
- 配置中间件和异常处理

#### config.py - 配置管理

集中管理所有配置项：
- 从环境变量加载配置
- 提供配置访问接口
- 管理后端服务 URL 映射

#### routes/ - 路由模块

每个路由文件负责：
- 定义 API 端点
- 处理请求参数
- 调用代理工具转发请求
- 返回响应结果

#### utils/proxy.py - 代理工具

封装通用的代理请求逻辑：
- 统一 HTTP 请求处理
- 异常处理和错误响应
- 日志记录

#### utils/logger.py - 日志工具

提供统一格式的日志记录器。

---

## 代码规范

### Python 代码规范

遵循 **PEP 8** 规范，并遵守以下约定：

#### 1. 命名规范

```python
# 类名：大驼峰
class GatewayConfig:
    pass

# 函数和变量：小写+下划线
def get_service_url():
    service_name = "a_stock"

# 常量：大写+下划线
TIMEOUT = 30
MAX_RETRIES = 3

# 私有成员：单下划线前缀
def _internal_method():
    pass
```

#### 2. 类型注解

所有函数必须使用类型注解：

```python
async def proxy_request(
    service_url: str,
    service_name: str,
    path: str = "/",
    method: str = "GET",
    params: dict = None,
    json_data: dict = None
) -> JSONResponse:
    pass
```

#### 3. 文档字符串

所有模块、类、函数使用文档字符串：

```python
def get_service_url(service_name: str) -> Optional[str]:
    """获取服务 URL

    Args:
        service_name: 服务名称（如 "a_stock", "hk_stock"）

    Returns:
        Optional[str]: 服务 URL，如果服务不存在则返回 None
    """
    pass
```

#### 4. 文件大小限制

- Python 文件不超过 **300 行**
- 如超过，考虑拆分为多个模块

#### 5. 导入顺序

```python
# 1. 标准库
import os
import sys
from datetime import datetime

# 2. 第三方库
from fastapi import APIRouter
from pydantic import BaseModel

# 3. 本地模块
from src.config import config
from src.utils.logger import setup_logger
```

### FastAPI 最佳实践

#### 1. 路由设计

```python
# 好的做法：路由命名清晰
@router.get("/api/a-stock")
async def get_a_stock() -> dict:
    pass

# 避免：过于复杂的逻辑
@router.get("/api/complex")
async def complex_endpoint():
    # 复杂的业务逻辑应该放在服务层
    pass
```

#### 2. 异常处理

```python
from fastapi import HTTPException

try:
    result = await some_operation()
if CustomError as e:
    raise HTTPException(
        status_code=400,
        detail=f"操作失败: {str(e)}"
    )
```

#### 3. 响应模型

使用 Pydantic 定义响应模型：

```python
from pydantic import BaseModel

class StockResponse(BaseModel):
    stock_code: str
    stock_name: str
    price: float
```

---

## 开发流程

### 1. 创建功能分支

```bash
git checkout -b feature/add-new-route
```

### 2. 编写代码

- 在 `src/routes/` 中创建新的路由文件
- 或修改现有文件添加新功能

### 3. 本地测试

```bash
# 启动开发服务器
uvicorn src.main:app --reload

# 测试 API
curl http://localhost:8010/health
```

### 4. 编写测试

在 `tests/` 目录下编写单元测试：

```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

### 5. 运行测试

```bash
pytest tests/
```

### 6. 提交代码

```bash
git add .
git commit -m "feat: 添加新服务路由"
git push origin feature/add-new-route
```

### 7. 创建 Pull Request

在 GitHub 上创建 PR，请求代码审查。

---

## 测试指南

### 测试框架

使用 **pytest** 作为测试框架。

### 安装测试依赖

```bash
uv pip install pytest pytest-asyncio httpx
```

### 测试结构

```
tests/
├── __init__.py
├── test_routes/           # 路由测试
│   ├── test_health.py
│   ├── test_a_stock.py
│   ├── test_hk_stock.py
│   └── test_news_analysis.py
├── test_utils/            # 工具测试
│   ├── test_proxy.py
│   └── test_logger.py
└── conftest.py            # pytest 配置
```

### 示例测试用例

#### 测试健康检查

```python
def test_health_check():
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "api-gateway"
    assert "version" in data
    assert "timestamp" in data
```

#### 测试代理功能

```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_proxy_request_success():
    """测试代理请求成功场景"""
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_get.return_value = mock_response

        from src.utils.proxy import proxy_request
        result = await proxy_request(
            service_url="http://test:8000",
            service_name="测试服务",
            path="/api/test"
        )

        assert result.status_code == 200
```

#### 测试异常处理

```python
def test_service_timeout():
    """测试服务超时异常"""
    with patch('src.utils.proxy.httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get.side_effect = \
            httpx.TimeoutException("Request timeout")

        from src.utils.proxy import proxy_request
        with pytest.raises(HTTPException) as exc_info:
            await proxy_request(
                service_url="http://test:8000",
                service_name="测试服务"
            )

        assert exc_info.value.status_code == 503
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行指定文件
pytest tests/test_routes/test_health.py

# 显示详细输出
pytest -v

# 显示代码覆盖率
pytest --cov=src --cov-report=html
```

---

## 调试技巧

### 1. 启用调试日志

在 `.env` 文件中设置：

```env
LOG_LEVEL=DEBUG
```

### 2. 使用 VS Code 调试器

创建 `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8010",
        "--reload"
      ],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### 3. 添加断点

在代码中添加断点：

```python
import pdb; pdb.set_trace()  # 传统方式
```

或使用 IDE 的可视化断点功能。

### 4. 查看日志

```bash
# Docker 环境
docker-compose logs -f api-gateway

# 本地环境
# 日志直接输出到控制台
```

### 5. 使用 FastAPI 自动文档

访问交互式 API 文档：

- Swagger UI: `http://localhost:8010/docs`
- ReDoc: `http://localhost:8010/redoc`

### 6. 网络调试

```bash
# 测试后端服务连通性
curl http://a-stock-service:8001/api/stocks

# 查看详细信息
curl -v http://localhost:8010/health

# 测试 POST 请求
curl -X POST http://localhost:8010/api/news-analysis \
  -H "Content-Type: application/json" \
  -d '{"text":"测试文本"}'
```

---

## 添加新服务路由

### 步骤 1: 在 config.py 中注册服务

编辑 `src/config.py`，在 `SERVICES` 字典中添加新服务：

```python
SERVICES: Dict[str, str] = {
    "a_stock": os.getenv("A_STOCK_SERVICE_URL", "http://a-stock-service:8001"),
    "hk_stock": os.getenv("HK_STOCK_SERVICE_URL", "http://hk-stock-service:8002"),
    "news_analysis": os.getenv("NEWS_ANALYSIS_SERVICE_URL", "http://news-analysis-service:8030"),
    "new_service": os.getenv("NEW_SERVICE_URL", "http://new-service:8004"),  # 新增
}
```

### 步骤 2: 在 .env.example 中添加配置

```env
NEW_SERVICE_URL=http://new-service:8004
```

### 步骤 3: 创建路由文件

创建 `src/routes/new_service.py`:

```python
"""
新服务路由
"""

from fastapi import APIRouter

from src.config import config
from src.utils.proxy import proxy_request
from src.utils.logger import setup_logger

router = APIRouter()
logger = setup_logger()


@router.get("/api/new-service")
async def get_new_service() -> dict:
    """代理新服务请求"""
    return await proxy_request(
        service_url=config.get_service_url("new_service"),
        service_name="新服务",
        path="/api/data"
    )
```

### 步骤 4: 在 main.py 中注册路由

编辑 `src/main.py`:

```python
from src.routes import health, a_stock, hk_stock, news_analysis, new_service

app.include_router(health.router)
app.include_router(a_stock.router)
app.include_router(hk_stock.router)
app.include_router(news_analysis.router)
app.include_router(new_service.router)  # 新增
```

### 步骤 5: 测试新路由

```bash
curl http://localhost:8010/api/new-service
```

---

## 常见开发任务

### 修改超时时间

编辑 `.env` 文件：

```env
TIMEOUT=60
```

### 修改日志级别

编辑 `.env` 文件：

```env
LOG_LEVEL=DEBUG  # 或 INFO, WARNING, ERROR
```

### 添加请求头转发

编辑 `src/utils/proxy.py`，在请求中添加自定义头：

```python
headers = {
    "X-Gateway-Version": config.VERSION,
    "X-Request-ID": generate_request_id()
}

response = await client.get(
    f"{service_url}{path}",
    params=params,
    headers=headers
)
```

### 添加请求验证

在路由中使用 Pydantic 验证请求参数：

```python
from pydantic import BaseModel, Field

class NewsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    date: str | None = Field(None, regex=r"\d{4}-\d{2}-\d{2}")

@router.post("/api/news-analysis")
async def analyze_news(request: NewsRequest) -> dict:
    return await proxy_request(
        service_url=config.get_service_url("news_analysis"),
        service_name="新闻分析",
        path="/api/analyze",
        method="POST",
        json_data=request.dict()
    )
```

### 添加速率限制

使用 slowapi 添加速率限制：

```bash
uv pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.get("/api/a-stock")
@limiter.limit("10/minute")
async def get_a_stock(request: Request) -> dict:
    pass
```

### 添加认证中间件

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != "expected-key":
        raise HTTPException(status_code=403, detail="Invalid API Key")

@router.get("/api/protected", dependencies=[Depends(verify_api_key)])
async def protected_route() -> dict:
    pass
```

---

## 代码审查清单

提交代码前，请确保：

- [ ] 代码符合 PEP 8 规范
- [ ] 所有函数都有类型注解
- [ ] 所有公共函数都有文档字符串
- [ ] 文件大小不超过 300 行
- [ ] 添加了相应的测试用例
- [ ] 测试全部通过
- [ ] 日志级别设置正确
- [ ] 环境变量已更新到 `.env.example`
- [ ] 没有硬编码的配置值
- [ ] 异常处理完善
- [ ] 没有引入安全漏洞

---

## 性能优化建议

### 1. 异步编程

确保所有 I/O 操作使用异步：

```python
# 好的做法
async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

# 避免
def fetch_data():
    response = requests.get(url)
```

### 2. 连接池复用

HTTPX 默认使用连接池，无需额外配置。

### 3. 避免同步阻塞

不要在异步函数中使用同步操作：

```python
# 避免
async def process():
    time.sleep(1)  # 同步阻塞

# 推荐
async def process():
    await asyncio.sleep(1)  # 异步等待
```

---

## 参考资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [PEP 8 编码规范](https://peps.python.org/pep-0008/)
- [pytest 文档](https://docs.pytest.org/)
- [HTTPX 文档](https://www.python-httpx.org/)

---

## 常见问题

### Q: 如何调试代理请求？

A: 启用 DEBUG 日志级别，查看详细的请求和响应信息。

### Q: 如何处理后端服务不可用？

A: 代理工具会自动捕获异常并返回 503 错误，可以在 `proxy.py` 中添加重试逻辑。

### Q: 如何添加新的 HTTP 方法（PUT, DELETE）？

A: 在 `proxy.py` 中的 `proxy_request` 函数已支持 PUT 和 DELETE，直接使用即可。

### Q: 如何监控 API 性能？

A: 可以集成 Prometheus 或添加自定义的性能日志记录。

---

**Happy Coding!** 🚀
