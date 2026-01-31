# 开发指南

## 目录

- [开发环境搭建](#开发环境搭建)
- [项目结构](#项目结构)
- [代码规范](#代码规范)
- [配置管理](#配置管理)
- [测试指南](#测试指南)
- [调试技巧](#调试技巧)
- [添加新服务](#添加新服务)
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

#### 6. 创建配置文件

```bash
cp config/services.yaml.example config/services.yaml
```

编辑 `config/services.yaml`，配置本地后端服务地址。

#### 7. 启动开发服务器

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8010 --reload
```

访问 `http://localhost:8010` 验证服务是否正常运行。

---

## 项目结构

```
api-gateway/
├── config/                     # 配置目录
│   ├── services.yaml           # 服务配置文件（核心）
│   └── services.yaml.example   # 配置文件示例
├── src/                        # 源代码目录
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── config.py               # 配置加载和验证
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   └── service_config.py   # 服务配置模型（RouteItem, ServiceItem, ServicesConfig）
│   ├── routes/                 # 路由模块
│   │   ├── __init__.py
│   │   └── health.py           # 健康检查路由
│   └── utils/                  # 工具模块
│       ├── __init__.py
│       ├── logger.py           # 日志工具
│       ├── proxy.py            # 代理工具
│       └── dynamic_router.py   # 动态路由注册器
├── tests/                      # 测试目录
├── docs/                       # 文档目录
├── scripts/                    # 运行脚本目录
├── .gitignore                  # Git 忽略规则
├── Dockerfile                  # Docker 镜像配置
├── docker-compose.yml          # Docker Compose 配置
├── requirements.txt            # Python 依赖列表
└── README.md                   # 项目说明
```

### 核心模块说明

#### main.py - 应用入口

FastAPI 应用的主入口文件，负责：
- 初始化 FastAPI 应用
- 动态注册路由（通过 `DynamicRouter`）
- 配置中间件和异常处理

**启动流程**:
1. 加载配置文件
2. 验证服务可达性
3. 动态注册所有路由
4. 启动服务

#### config.py - 配置管理

集中管理所有配置项：
- 从 YAML 文件加载服务配置
- 验证配置文件格式
- 验证服务可达性（健康检查）
- 提供配置访问接口

#### models/service_config.py - 数据模型

定义配置数据模型：
- `RouteItem`: 路由配置项（path, method, backend_path）
- `ServiceItem`: 单个服务配置（url, enabled, health_path, routes）
- `ServicesConfig`: 服务配置集合

使用 Pydantic 进行数据验证。

#### utils/dynamic_router.py - 动态路由注册器

根据配置文件动态注册路由：
- 读取配置中的所有路由
- 为每个路由生成处理函数
- 自动注册到 FastAPI 应用

**无需手动编写路由文件**，所有路由由配置驱动。

#### utils/proxy.py - 代理工具

封装通用的代理请求逻辑：
- 统一 HTTP 请求处理
- 支持 GET/POST/PUT/DELETE/PATCH
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
from typing import Optional

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
        Optional[str]: 服务 URL，如果服务不存在或未启用则返回 None
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

---

## 配置管理

### 服务配置文件结构

`config/services.yaml`:

```yaml
services:
  # 服务唯一标识
  <service_name>:
    url: <backend_service_url>       # 后端服务地址
    enabled: true|false               # 是否启用
    health_path: /health              # 健康检查路径
    routes:                           # 路由列表
      - path: /api/gateway-path       # 网关路径
        method: GET|POST|PUT|DELETE   # HTTP 方法
        backend_path: /api/backend    # 后端路径（可选）
```

### 配置验证

网关启动时自动验证：
1. 配置文件格式（YAML 语法）
2. 必填字段完整性
3. 服务 URL 格式合法性
4. 后端服务可达性

### 添加新服务（无需修改代码）

**步骤 1**: 编辑 `config/services.yaml`

```yaml
services:
  n8n_webhook:
    url: http://n8n:5678
    enabled: true
    health_path: /healthz
    routes:
      - path: /api/webhook/test
        method: POST
        backend_path: /webhook/test
```

**步骤 2**: 重启网关

```bash
docker-compose restart api-gateway
```

**步骤 3**: 验证新服务

```bash
curl -X POST http://localhost:8010/api/webhook/test
```

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
├── test_models/              # 模型测试
│   ├── test_service_config.py
│   └── test_route_item.py
├── test_utils/               # 工具测试
│   ├── test_proxy.py
│   ├── test_logger.py
│   └── test_dynamic_router.py
└── conftest.py               # pytest 配置
```

### 示例测试用例

#### 测试配置模型

```python
def test_service_item_validation():
    """测试服务配置验证"""
    from src.models.service_config import ServiceItem

    # 有效配置
    service = ServiceItem(
        url="http://localhost:8000",
        enabled=True,
        routes=[]
    )
    assert service.url == "http://localhost:8000"

    # 无效 URL
    with pytest.raises(ValueError):
        ServiceItem(url="invalid-url")

def test_route_item_validation():
    """测试路由配置验证"""
    from src.models.service_config import RouteItem

    route = RouteItem(
        path="/api/test",
        method="GET"
    )
    assert route.path == "/api/test"
    assert route.method == "GET"
```

#### 测试健康检查

```python
def test_health_check():
    """测试健康检查端点"""
    from fastapi.testclient import TestClient
    from src.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "api-gateway"
    assert "version" in data
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行指定文件
pytest tests/test_models/test_service_config.py

# 显示详细输出
pytest -v

# 显示代码覆盖率
pytest --cov=src --cov-report=html
```

---

## 调试技巧

### 1. 启用调试日志

在环境变量中设置：

```bash
export LOG_LEVEL=DEBUG
```

或在 `.env` 文件中：

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

### 3. 查看日志

```bash
# Docker 环境
docker-compose logs -f api-gateway

# 本地环境
# 日志直接输出到控制台
```

### 4. 使用 FastAPI 自动文档

访问交互式 API 文档：

- Swagger UI: `http://localhost:8010/docs`
- ReDoc: `http://localhost:8010/redoc`

### 5. 网络调试

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

## 添加新服务

### 方式一：通过配置文件（推荐）

**无需修改代码**，仅需三步：

#### 步骤 1: 编辑配置文件

`config/services.yaml`:

```yaml
services:
  new_service:
    url: http://new-service:8000
    enabled: true
    health_path: /health
    routes:
      - path: /api/new-endpoint
        method: POST
        backend_path: /api/real-endpoint
```

#### 步骤 2: 重启网关

```bash
docker-compose restart api-gateway
```

#### 步骤 3: 验证

```bash
curl -X POST http://localhost:8010/api/new-endpoint
```

### 方式二：扩展功能（需要代码修改）

如果需要添加特殊逻辑（如参数验证、请求转换），可以扩展 `dynamic_router.py` 或创建自定义工具函数。

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

编辑 `src/utils/dynamic_router.py`，在代理请求中添加自定义头：

```python
headers = {
    "X-Gateway-Version": config.VERSION,
    "X-Request-ID": generate_request_id()
}

response = await client.post(
    url,
    json=json_data,
    headers=headers
)
```

### 添加请求验证

由于使用动态路由，请求验证需要在代理层面实现。可以扩展 `dynamic_router.py` 添加通用的验证逻辑。

### 添加速率限制

使用 slowapi 添加速率限制：

```bash
uv pip install slowapi
```

在 `main.py` 中添加：

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

在 `dynamic_router.py` 的路由处理函数中添加：

```python
@limiter.limit("10/minute")
async def route_handler(request: Request):
    # ...
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

A: 代理工具会自动捕获异常并返回 503 错误，可以在配置中设置 `enabled: false` 临时禁用服务。

### Q: 如何添加新的 HTTP 方法？

A: 在配置文件的 `routes` 中指定 `method` 字段，支持 GET/POST/PUT/DELETE/PATCH。

### Q: 如何监控 API 性能？

A: 可以集成 Prometheus 或添加自定义的性能日志记录。

### Q: 配置文件修改后需要重启吗？

A: 是的，当前版本需要重启服务以加载新配置。

---

**Happy Coding!** 🚀
