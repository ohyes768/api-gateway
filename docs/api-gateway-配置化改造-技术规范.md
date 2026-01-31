# API Gateway 配置化改造技术规范

## 1. 概述

### 1.1 背景
当前 API Gateway 的服务 URL 配置分散在环境变量和代码中（`config.py`），添加新服务需要修改代码、创建路由文件、在 `main.py` 中注册路由，操作繁琐且不够灵活。

### 1.2 目标
- **核心目标**：通过 YAML 配置文件管理后端服务，实现服务的动态配置，无需修改代码即可添加/删除/修改服务
- **附加目标**：启动时验证配置文件格式和服务可达性，确保配置正确性
- **非目标**：不涉及路由规则配置化（路径映射保持代码硬编码）、不支持负载均衡、熔断降级等高级功能

### 1.3 适用场景
- 需要频繁添加/删除/修改后端服务的场景
- 多环境部署（开发、测试、生产）需要不同的服务配置
- 不希望为了添加服务而修改代码和重新构建镜像的场景

## 2. 功能需求

### 2.1 核心功能
1. **YAML 配置文件管理**
   - 配置文件路径：`config/services.yaml`
   - 支持服务名称、URL、启用状态的配置
   - 配置文件不存在时拒绝启动

2. **启动时验证**
   - 验证 YAML 文件格式是否正确
   - 验证必填字段是否完整
   - 验证服务 URL 格式是否合法
   - 验证服务可达性（调用健康检查端点）

3. **服务路由**
   - 路由路径在代码中硬编码（如 `/api/news-analysis`）
   - 根据配置文件中的服务 URL 动态转发请求
   - 支持服务启用/禁用状态控制

4. **全局配置**
   - 全局超时时间（环境变量 `TIMEOUT`）
   - 日志级别（环境变量 `LOG_LEVEL`）

### 2.2 用户故事

**场景 1：添加新服务**
```
用户：运维人员
目标：添加一个新的后端服务
操作：
1. 编辑 config/services.yaml，添加服务配置
2. 重启网关服务
3. 网关启动时验证新服务可达性
4. 服务自动加入路由
```

**场景 2：修改服务 URL**
```
用户：运维人员
目标：将某服务迁移到新地址
操作：
1. 编辑 config/services.yaml，修改服务 URL
2. 重启网关服务
3. 网关自动使用新地址转发请求
```

**场景 3：临时禁用服务**
```
用户：运维人员
目标：临时下线某服务进行维护
操作：
1. 编辑 config/services.yaml，将服务 enabled 设为 false
2. 重启网关服务
3. 该服务返回 503 不可用
```

## 3. 技术决策

### 3.1 技术栈
- **Python 版本**：3.10+
- **Web 框架**：FastAPI 0.104+
- **YAML 解析库**：PyYAML（标准库，成熟稳定）
- **HTTP 客户端**：HTTPX（异步支持）
- **配置验证**：Pydantic（数据验证）

### 3.2 架构设计

#### 配置文件结构
```yaml
# config/services.yaml
services:
  news_analysis:
    url: http://news-analysis-service:8030
    enabled: true
    health_path: /health  # 可选，默认 /health

  a_stock:
    url: http://a-stock-service:8001
    enabled: true

  hk_stock:
    url: http://hk-stock-service:8002
    enabled: true
```

#### 目录结构
```
api-gateway/
├── config/
│   └── services.yaml              # 服务配置文件
├── src/
│   ├── main.py                    # FastAPI 主入口
│   ├── config.py                  # 配置加载和验证
│   ├── models/
│   │   └── service_config.py      # 服务配置数据模型
│   ├── routes/
│   │   ├── health.py              # 健康检查
│   │   ├── a_stock.py             # A股路由
│   │   ├── hk_stock.py            # 港股路由
│   │   └── news_analysis.py       # 新闻分析路由
│   └── utils/
│       ├── logger.py              # 日志工具
│       └── proxy.py               # 代理工具
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

#### 配置加载流程
```
1. 应用启动
   ↓
2. 加载 config/services.yaml
   ↓
3. 解析 YAML 内容
   ↓
4. 使用 Pydantic 验证配置格式
   ↓
5. 验证每个服务的 URL 格式
   ↓
6. 并发检查所有 enabled=true 的服务可达性
   ↓
7. 构建服务注册表
   ↓
8. 启动 FastAPI 应用
```

#### 请求转发流程
```
1. 客户端请求 → Gateway (/api/news-analysis)
   ↓
2. 路由匹配（代码中硬编码）
   ↓
3. 从配置中获取服务 URL
   ↓
4. 检查服务 enabled 状态
   ├─ enabled=false → 返回 503 服务不可用
   └─ enabled=true → 继续
   ↓
5. 转发请求到后端服务
   ↓
6. 返回响应给客户端
```

### 3.3 方案权衡记录

| 方案 | 优点 | 缺点 | 最终选择 |
|------|------|------|----------|
| **YAML vs JSON** | YAML 易读、支持注释<br>JSON 简单、原生支持 | YAML 需要额外库<br>JSON 不易读 | **YAML**（易读性和注释支持更重要） |
| **PyYAML vs Ruamel** | 成熟稳定、文档丰富 | 不保留格式和注释 | **PyYAML**（标准库，足够用） |
| **启动时验证 vs 延迟验证** | 确保启动后服务可用<br>快速失败原则 | 启动时间稍长 | **启动时验证**（可用性优先） |
| **热重载 vs 重启** | 无需重启即可更新配置<br>运行时更新服务 | 实现复杂度高<br>可能出现不一致状态 | **重启加载**（简单可靠） |
| **硬编码路由 vs 配置化路由** | 简单直接<br>类型安全<br>IDE 支持 | 不够灵活 | **硬编码路由**（用户明确要求） |
| **保留环境变量 vs 仅配置文件** | 向后兼容<br>灵活性高 | 配置分散<br>维护成本高 | **仅配置文件**（简化配置） |

## 4. 数据设计

### 4.1 数据模型

#### ServiceConfig（服务配置模型）
```python
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Dict, List

class ServiceItem(BaseModel):
    """单个服务配置"""
    url: HttpUrl = Field(..., description="服务 URL")
    enabled: bool = Field(default=True, description="是否启用")
    health_path: str = Field(default="/health", description="健康检查路径")

    @validator('url')
    def validate_url(cls, v):
        """验证 URL 格式"""
        if not str(v).startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class ServicesConfig(BaseModel):
    """服务配置集合"""
    services: Dict[str, ServiceItem] = Field(..., description="服务配置字典")

    @validator('services')
    def validate_services_not_empty(cls, v):
        """至少配置一个服务"""
        if not v:
            raise ValueError('At least one service must be configured')
        return v
```

#### Config（全局配置类）
```python
class Config:
    """应用配置类"""
    LOG_LEVEL: str
    TIMEOUT: int
    APP_NAME: str = "API Gateway"
    VERSION: str = "2.1.0"

    # 服务配置（从 YAML 加载）
    services_config: ServicesConfig

    def __init__(self, config_path: str = "config/services.yaml"):
        """加载并验证配置"""
        self._load_services_config(config_path)
        self._validate_services_reachability()

    def _load_services_config(self, config_path: str):
        """加载服务配置文件"""
        # 实现见第 5 节

    def _validate_services_reachability(self):
        """验证服务可达性"""
        # 实现见第 5 节
```

### 4.2 状态管理

#### 配置加载状态
- **未加载**：应用启动前
- **加载中**：正在读取和验证配置
- **已加载**：配置验证通过，服务可用
- **加载失败**：配置文件不存在或验证失败，应用拒绝启动

#### 服务可用性状态
- **启用**：`enabled=true` 且健康检查通过
- **禁用**：`enabled=false`
- **不可用**：`enabled=true` 但健康检查失败

## 5. 核心实现

### 5.1 配置加载模块（`src/config.py`）

```python
"""
API Gateway 配置管理
从 YAML 配置文件加载服务配置
"""

import os
from pathlib import Path
from typing import Optional, Dict
import yaml
import httpx
from src.models.service_config import ServicesConfig

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
        self._validate_services_reachability()

    def _load_services_config(self, config_path: str):
        """加载服务配置文件"""
        config_file = Path(config_path)

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
            return str(service.url)
        return None


# 全局配置实例
config = Config()
```

### 5.2 配置数据模型（`src/models/service_config.py`）

```python
"""
服务配置数据模型
"""

from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Dict, Optional


class ServiceItem(BaseModel):
    """单个服务配置"""

    url: HttpUrl = Field(..., description="服务 URL")
    enabled: bool = Field(default=True, description="是否启用")
    health_path: str = Field(
        default="/health",
        description="健康检查路径"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "http://news-analysis-service:8030",
                "enabled": True,
                "health_path": "/health"
            }
        }

    @validator('url')
    def validate_url(cls, v):
        """验证 URL 格式"""
        url_str = str(v)
        if not url_str.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')

        # 检查是否包含主机和端口
        from urllib.parse import urlparse
        parsed = urlparse(url_str)
        if not parsed.netloc:
            raise ValueError('Invalid URL format')

        return v

    @validator('health_path')
    def validate_health_path(cls, v):
        """验证健康检查路径"""
        if not v.startswith('/'):
            raise ValueError('health_path must start with /')
        return v


class ServicesConfig(BaseModel):
    """服务配置集合"""

    services: Dict[str, ServiceItem] = Field(
        ...,
        description="服务配置字典，key 为服务名称"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "services": {
                    "news_analysis": {
                        "url": "http://news-analysis-service:8030",
                        "enabled": True,
                        "health_path": "/health"
                    },
                    "a_stock": {
                        "url": "http://a-stock-service:8001",
                        "enabled": True
                    }
                }
            }
        }

    @validator('services')
    def validate_services_not_empty(cls, v):
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
```

### 5.3 路由模块更新（`src/routes/news_analysis.py`）

```python
"""
新闻分析服务路由
"""

from fastapi import APIRouter, Body, HTTPException, status

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

    Raises:
        HTTPException: 服务未启用或不可用时
    """
    # 获取服务 URL
    service_url = config.get_service_url("news_analysis")

    if not service_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="新闻分析服务未启用或不可用"
        )

    return await proxy_request(
        service_url=service_url,
        service_name="新闻分析",
        path="/api/analyze",
        method="POST",
        json_data={"text": text}
    )
```

### 5.4 配置文件示例（`config/services.yaml`）

```yaml
# API Gateway 服务配置
# 修改此文件后需要重启网关服务

services:
  # 新闻分析服务
  news_analysis:
    url: http://news-analysis-service:8030
    enabled: true
    health_path: /health

  # A股新股信息服务
  a_stock:
    url: http://a-stock-service:8001
    enabled: true
    health_path: /health

  # 港股新股信息服务
  hk_stock:
    url: http://hk-stock-service:8002
    enabled: true
    health_path: /health
```

### 5.5 依赖更新（`requirements.txt`）

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.27.0
pydantic>=2.0
pyyaml>=6.0
python-dotenv>=1.0
loguru>=0.7
```

## 6. 非功能需求

### 6.1 性能要求
- **启动时间**：启动时验证所有服务可达性，预计增加 5-10 秒（取决于服务数量）
- **请求转发延迟**：增加 < 10ms（仅增加配置查询开销）
- **并发支持**：支持至少 1000 并发请求

### 6.2 安全要求
- **URL 验证**：严格验证 URL 格式，防止 SSRF 攻击
- **配置文件权限**：配置文件应由服务账号管理，避免权限泄露
- **错误信息**：不在错误信息中暴露内部服务地址

### 6.3 可维护性
- **配置验证**：启动时完整验证配置，快速失败
- **错误提示**：清晰的配置错误提示，指出具体错误位置
- **日志记录**：配置加载和服务可达性检查的详细日志
- **文档完善**：配置文件格式说明和示例

## 7. 边缘情况与错误处理

### 7.1 异常场景

#### 配置文件不存在
```python
# 错误处理
raise FileNotFoundError(
    f"配置文件不存在: {config_path}\n"
    f"请创建配置文件并配置服务信息。"
)
# 应用拒绝启动
```

#### YAML 格式错误
```python
# 错误处理
try:
    config_data = yaml.safe_load(f)
except yaml.YAMLError as e:
    raise ValueError(f"YAML 格式错误: {e}")
# 指出具体错误行和列
```

#### 服务 URL 不可达
```python
# 错误处理
if response.status_code != 200:
    raise ValueError(
        f"服务 '{name}' 健康检查失败 "
        f"({health_url}): {response.status_code}"
    )
# 应用拒绝启动
```

#### 服务运行时不可用
```python
# 路由处理
service_url = config.get_service_url("news_analysis")
if not service_url:
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="新闻分析服务未启用或不可用"
    )
```

### 7.2 边界条件

#### 空配置文件
```yaml
services: {}
```
**处理**：启动时验证至少需要一个服务配置

#### 所有服务禁用
```yaml
services:
  news_analysis:
    url: http://news-analysis-service:8030
    enabled: false
```
**处理**：允许启动，但所有路由返回 503

#### URL 格式错误
```yaml
services:
  news_analysis:
    url: invalid-url  # 缺少协议
```
**处理**：Pydantic 验证失败，启动时报错

#### 网络分区
**场景**：启动时后端服务临时不可用
**处理**：应用拒绝启动，确保只有配置正确的服务才会启动

### 7.3 降级策略

#### 启动时降级
- **不支持降级**：严格模式，配置或服务不可达时拒绝启动
- **理由**：快速失败原则，避免运行时才发现服务不可用

#### 运行时降级
- **服务暂时不可用**：路由返回 503，客户端重试
- **建议**：客户端实现指数退避重试机制

## 8. 实施计划

### 8.1 开发阶段

#### 阶段 1：数据模型和配置加载（优先级：高）
- [ ] 创建 `src/models/service_config.py`
- [ ] 实现 `ServiceItem` 和 `ServicesConfig` 模型
- [ ] 编写单元测试验证模型

#### 阶段 2：配置加载和验证（优先级：高）
- [ ] 重构 `src/config.py`
- [ ] 实现 YAML 配置加载
- [ ] 实现服务可达性验证
- [ ] 编写集成测试

#### 阶段 3：路由模块更新（优先级：中）
- [ ] 更新 `src/routes/news_analysis.py`
- [ ] 更新 `src/routes/a_stock.py`
- [ ] 更新 `src/routes/hk_stock.py`
- [ ] 添加服务未启用时的错误处理

#### 阶段 4：配置文件和文档（优先级：中）
- [ ] 创建 `config/services.yaml.example`
- [ ] 更新 README.md
- [ ] 编写配置说明文档

#### 阶段 5：测试和优化（优先级：低）
- [ ] 端到端测试
- [ ] 性能测试
- [ ] 错误场景测试

### 8.2 测试策略

#### 单元测试
```python
# tests/test_service_config.py
def test_service_item_validation():
    """测试服务配置验证"""
    # 有效配置
    service = ServiceItem(
        url="http://localhost:8000",
        enabled=True
    )
    assert service.url == "http://localhost:8000"

    # 无效 URL
    with pytest.raises(ValueError):
        ServiceItem(url="invalid-url")

def test_services_config_not_empty():
    """测试至少需要一个服务"""
    with pytest.raises(ValueError):
        ServicesConfig(services={})
```

#### 集成测试
```python
# tests/test_config_loading.py
async def test_load_valid_config():
    """测试加载有效配置"""
    config = Config("tests/fixtures/valid_config.yaml")
    assert config.services_config is not None
    assert len(config.services_config.services) > 0

async def test_config_file_not_found():
    """测试配置文件不存在"""
    with pytest.raises(FileNotFoundError):
        Config("nonexistent.yaml")
```

#### 端到端测试
```bash
# 1. 启动测试后端服务
docker-compose up -d mock-backend

# 2. 使用测试配置启动网关
docker-compose -f docker-compose.test.yml up gateway

# 3. 验证路由转发
curl http://localhost:8000/api/news-analysis \
  -d '{"text":"测试文本"}'

# 4. 验证响应正确
```

### 8.3 部署计划

#### 部署环境
- **开发环境**：本地 Docker Compose
- **测试环境**：服务器 Docker Compose
- **生产环境**：服务器 Docker Compose

#### 部署流程
```bash
# 1. 备份当前环境配置
cp config/services.yaml config/services.yaml.bak

# 2. 更新代码
git pull origin main

# 3. 更新配置文件
vi config/services.yaml

# 4. 重新构建镜像
docker-compose build gateway

# 5. 重启网关服务
docker-compose up -d gateway

# 6. 验证服务正常
docker logs -f gateway
curl http://localhost:8000/health
```

#### 回滚方案
```bash
# 如果新版本有问题，快速回滚
git checkout <previous-tag>
docker-compose build gateway
docker-compose up -d gateway
```

## 9. 风险与依赖

### 9.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| YAML 解析库漏洞 | 高 | 低 | 使用成熟稳定的 PyYAML，定期更新依赖 |
| 启动时间过长 | 中 | 中 | 并发检查服务可达性，设置合理超时 |
| 配置文件格式错误导致服务不可用 | 高 | 高 | 启动时严格验证，提供配置示例和校验工具 |
| 网络分区导致启动失败 | 中 | 中 | 提供明确的错误提示和重试机制 |

### 9.2 外部依赖
- **PyYAML**：YAML 解析库（MIT 许可）
- **httpx**：异步 HTTP 客户端（MIT 许可）
- **Pydantic**：数据验证库（MIT 许可）

### 9.3 团队依赖
- **运维人员**：需要了解 YAML 配置文件格式
- **开发人员**：需要了解新的配置加载机制

## 10. 附录

### 10.1 用户访谈记录

#### 关键决策点

**Q1: 配置范围（服务 URL vs 完整路由）**
- **用户选择**：仅服务发现（服务 URL 可配置）
- **理由**：路由规则相对固定，不需要频繁修改

**Q2: 配置方式（YAML vs JSON vs 数据库）**
- **用户选择**：YAML 配置文件
- **理由**：易读、支持注释、易于版本控制

**Q3: 配置文件位置**
- **用户选择**：config/services.yaml
- **理由**：独立配置目录，结构清晰

**Q4: URL 验证方式**
- **用户选择**：格式验证 + 可达性检查
- **理由**：确保启动后服务可用，快速失败

**Q5: 热重载支持**
- **用户选择**：不支持热重载
- **理由**：简单可靠，重启开销可接受

### 10.2 配置迁移指南

#### 从环境变量迁移到 YAML

**旧配置（`.env`）**
```bash
A_STOCK_SERVICE_URL=http://a-stock-service:8001
HK_STOCK_SERVICE_URL=http://hk-stock-service:8002
NEWS_ANALYSIS_SERVICE_URL=http://news-analysis-service:8030
```

**新配置（`config/services.yaml`）**
```yaml
services:
  a_stock:
    url: http://a-stock-service:8001
    enabled: true

  hk_stock:
    url: http://hk-stock-service:8002
    enabled: true

  news_analysis:
    url: http://news-analysis-service:8030
    enabled: true
```

**迁移步骤**
1. 创建 `config/services.yaml`
2. 将 `.env` 中的服务 URL 转换为 YAML 格式
3. 删除 `.env` 中的服务 URL 配置
4. 重启服务验证

### 10.3 配置文件校验工具

为了方便验证配置文件，可以提供校验工具：

```python
# scripts/validate_config.py
"""配置文件校验工具"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config

def main():
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config/services.yaml"

    try:
        print(f"正在验证配置文件: {config_file}")
        config = Config(config_file)

        print("✅ 配置文件验证通过！")
        print(f"\n已配置的服务:")
        for name, service in config.services_config.services.items():
            status = "启用" if service.enabled else "禁用"
            print(f"  - {name}: {service.url} [{status}]")

    except Exception as e:
        print(f"❌ 配置文件验证失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**使用方法**
```bash
python scripts/validate_config.py config/services.yaml
```

### 10.4 参考资料

- [PyYAML 文档](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [HTTPX 文档](https://www.python-httpx.org/)

### 10.5 术语表

| 术语 | 说明 |
|------|------|
| 服务发现 | 动态获取后端服务 URL 的机制 |
| 健康检查 | 通过访问 `/health` 端点验证服务是否可用 |
| 热重载 | 运行时重新加载配置，无需重启服务 |
| SSRF | Server-Side Request Forgery，服务端请求伪造攻击 |
| YAML | YAML Ain't Markup Language，一种人类友明的配置文件格式 |
| Pydantic | Python 数据验证库，使用类型注解进行数据验证 |
