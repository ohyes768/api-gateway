# 新服务接入指南

本文档说明如何开发一个新的微服务并接入 API Gateway。

## 目录

- [概述](#概述)
- [服务开发规范](#服务开发规范)
- [Docker 配置](#docker-配置)
- [网络配置](#网络配置)
- [API Gateway 配置](#api-gateway-配置)
- [部署流程](#部署流程)
- [测试验证](#测试验证)
- [示例项目](#示例项目)

## 概述

新服务接入 API Gateway 需要完成以下步骤：

1. 开发符合规范的微服务
2. 编写 Dockerfile 和 docker-compose.yml
3. 配置容器网络连接 API Gateway
4. 在 API Gateway 中配置路由
5. 部署并验证

## 服务开发规范

### 1. 技术栈要求

- **容器化**：必须支持 Docker 部署
- **健康检查**：必须提供 `/health` 端点
- **日志规范**：使用标准输出（stdout），JSON 格式推荐
- **配置管理**：支持环境变量配置

### 2. API 设计规范

#### RESTful API 设计

```python
# 示例：FastAPI 服务
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    """健康检查端点（必需）"""
    return {"status": "healthy"}

@app.get("/api/items")
async def list_items():
    """业务 API"""
    return {"items": []}
```

#### 健康检查规范

所有服务**必须**提供健康检查端点：

```yaml
# 健康检查响应规范
{
  "status": "healthy",  # 或 "unhealthy"
  "timestamp": "2026-01-31T12:00:00Z"
}
```

### 3. 项目结构建议

```
my-service/
├── backend/
│   └── my_service/         # 服务代码
│       ├── main.py
│       ├── Dockerfile
│       └── requirements.txt
├── docker/
│   └── docker-compose.yml  # Docker Compose 配置
└── config/
    └── service.yaml        # 服务配置（可选）
```

## Docker 配置

### 1. Dockerfile 示例

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 关键配置项

```dockerfile
# 1. 工作目录
WORKDIR /app

# 2. 暴露端口（与实际服务端口一致）
EXPOSE 8000

# 3. 健康检查（推荐添加）
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

## 网络配置

### 重要：容器网络配置

**核心原则**：新服务必须与 API Gateway 在**同一个 Docker 网络**中。

### 方案：使用外部网络

#### 1. 创建共享网络

```bash
# 创建外部网络（只需执行一次）
docker network create api-gateway_api-network
```

#### 2. 配置 docker-compose.yml

```yaml
version: '3.8'

services:
  my-service:
    build:
      context: ../backend/my_service
      dockerfile: Dockerfile
    container_name: my-service  # 重要：作为 DNS 主机名
    ports:
      - "8010:8000"  # 宿主机端口:容器端口
    environment:
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - TIMEOUT=${TIMEOUT:-30}
    networks:
      - api-network  # 加入 API Gateway 的网络
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

# 使用外部网络
networks:
  api-network:
    name: api-gateway_api-network  # 指定 API Gateway 的网络名
    external: true  # 声明为外部网络
```

#### 3. 网络配置说明

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| `container_name` | 容器名称，也是 DNS 主机名 | `my-service` |
| `networks` | 服务加入的网络 | `api-network` |
| `name` | 实际的 Docker 网络名 | `api-gateway_api-network` |
| `external: true` | 使用外部已存在的网络 | `true` |

#### 4. 验证网络连接

```bash
# 查看网络中的容器
docker network inspect api-gateway_api-network

# 从 API Gateway 容器测试连接
docker exec api-gateway ping -c 2 my-service
docker exec api-gateway curl http://my-service:8000/health
```

## API Gateway 配置

### 1. 修改 services.yaml

在 API Gateway 项目的 `config/services.yaml` 中添加新服务配置：

```yaml
services:
  # 现有服务...

  # 新服务
  my_service:
    url: http://my-service:8000  # 容器名:端口
    enabled: true
    health_path: /health
    routes:
      - path: /api/my-service/items
        method: GET
        backend_path: /api/items

      - path: /api/my-service/create
        method: POST
        backend_path: /api/create
```

### 2. 配置字段说明

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `url` | string | ✅ | 服务地址，格式：`http://容器名:端口` |
| `enabled` | boolean | ✅ | 是否启用该服务 |
| `health_path` | string | ✅ | 健康检查路径 |
| `routes` | array | ✅ | 路由配置列表 |
| `routes[].path` | string | ✅ | 外部访问路径 |
| `routes[].method` | string | ✅ | HTTP 方法：GET/POST/PUT/DELETE |
| `routes[].backend_path` | string | ✅ | 后端实际路径 |

### 3. 路由映射规则

```
外部请求：http://api-gateway:8010/api/my-service/items
         ↓
API Gateway 转发
         ↓
内部请求：http://my-service:8000/api/items
```

## 部署流程

### 完整部署步骤

```bash
# ===== 第一步：开发新服务 =====
cd my-service/

# 确保 Dockerfile 和代码就绪
ls backend/my_service/Dockerfile

# ===== 第二步：配置网络 =====
# 创建或加入 API Gateway 的网络
docker network create api-gateway_api-network

# 编辑 docker-compose.yml，配置外部网络
cd docker/
vi docker-compose.yml
# 确保 networks 部分配置为：
# networks:
#   api-network:
#     name: api-gateway_api-network
#     external: true

# ===== 第三步：启动新服务 =====
docker-compose up -d --build

# 验证服务启动
docker ps | grep my-service
docker logs my-service

# ===== 第四步：配置 API Gateway =====
cd /path/to/api-gateway

# 编辑配置文件
vi config/services.yaml
# 添加新服务配置（见上文）

# 重新构建 API Gateway
docker-compose build
docker-compose up -d

# ===== 第五步：验证路由 =====
# 查看日志，确认路由已注册
docker logs api-gateway | grep "注册路由"

# 测试访问
curl http://localhost:8010/api/my-service/items
```

## 测试验证

### 1. 健康检查

```bash
# 检查新服务健康状态
docker exec my-service curl http://localhost:8000/health

# 从 API Gateway 检查连接
docker exec api-gateway curl http://my-service:8000/health
```

### 2. 路由测试

```bash
# 直接访问服务（绕过网关）
curl http://localhost:8010/api/items

# 通过 API Gateway 访问
curl http://localhost:8010/api/my-service/items
```

### 3. 日志查看

```bash
# 查看服务日志
docker logs -f my-service

# 查看 API Gateway 日志
docker logs -f api-gateway

# 查看 API Gateway 路由注册日志
docker logs api-gateway | grep "注册路由"
```

### 4. 网络验证

```bash
# 查看网络详情
docker network inspect api-gateway_api-network

# 检查容器是否在同一网络
docker network inspect api-gateway_api-network | grep -A 2 "Containers"

# 测试 DNS 解析
docker exec api-gateway nslookup my-service
```

## 示例项目

### 完整示例：新闻分析服务

#### 1. 服务代码（backend/news_analysis_service/main.py）

```python
from fastapi import FastAPI

app = FastAPI(title="News Analysis Service")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "news-analysis"}

@app.post("/analyze/markdown")
async def analyze_markdown(request: dict):
    content = request.get("content", "")
    # 业务逻辑...
    return {"result": "analysis completed"}
```

#### 2. Dockerfile

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8030
HEALTHCHECK CMD curl -f http://localhost:8030/health || exit 1
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8030"]
```

#### 3. docker-compose.yml

```yaml
version: '3.8'

services:
  news-analysis-service:
    build:
      context: ../backend/news_analysis_service
      dockerfile: Dockerfile
    container_name: news-analysis-service
    ports:
      - "8030:8030"
    environment:
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    networks:
      - api-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8030/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  api-network:
    name: api-gateway_api-network
    external: true
```

#### 4. API Gateway 配置

```yaml
services:
  news_analysis:
    url: http://news-analysis-service:8030
    enabled: true
    health_path: /health
    routes:
      - path: /api/news-analysis/markdown
        method: POST
        backend_path: /analyze/markdown
```

#### 5. 测试

```bash
# 启动服务
cd docker/
docker-compose up -d

# 配置 API Gateway
cd /path/to/api-gateway
vi config/services.yaml  # 添加配置
docker-compose restart

# 测试
curl -X POST http://localhost:8010/api/news-analysis/markdown \
  -H "Content-Type: application/json" \
  -d '{"content": "测试内容", "date": "2026-01-31"}'
```

## 常见问题

### 1. DNS 解析失败

**错误**：`Name or service not known`

**原因**：容器不在同一网络中

**解决**：
```bash
# 检查网络配置
docker network inspect api-gateway_api-network

# 确保两个服务的 docker-compose.yml 都配置了：
networks:
  api-network:
    name: api-gateway_api-network
    external: true
```

### 2. 404 Not Found

**错误**：路由注册成功但访问 404

**原因**：`backend_path` 配置错误

**解决**：
```bash
# 进入容器测试实际路径
docker exec my-service curl http://localhost:8000/api/items

# 修改 services.yaml 中的 backend_path
```

### 3. 服务请求超时

**错误**：`服务请求超时`

**解决**：
```yaml
# 在 docker-compose.yml 中增加超时配置
environment:
  - TIMEOUT=60  # 增加到 60 秒
```

### 4. 网络冲突

**错误**：创建网络失败

**解决**：
```bash
# 查看现有网络
docker network ls

# 使用现有网络或删除重建
docker network rm old-network
docker network create api-gateway_api-network
```

## 最佳实践

### 1. 命名规范

- **容器名**：使用小写字母和连字符，如 `news-analysis-service`
- **服务名**：使用下划线，如 `news_analysis`
- **网络名**：使用项目前缀，如 `api-gateway_api-network`

### 2. 配置管理

- 敏感信息使用环境变量
- 配置文件不要提交到 Git（使用 `.env.example`）
- 支持默认值：`${VAR:-default}`

### 3. 健康检查

- 必须提供 `/health` 端点
- 响应时间 < 1 秒
- 返回 JSON 格式

### 4. 日志规范

```python
import logging

logger = logging.getLogger(__name__)
logger.info("用户请求", extra={"user_id": 123})
```

### 5. 错误处理

```python
from fastapi import HTTPException

@app.get("/api/items")
async def get_items():
    try:
        # 业务逻辑
        return items
    except Exception as e:
        logger.error(f"获取列表失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务错误")
```

## 检查清单

部署新服务前，确保完成以下检查：

- [ ] 服务提供 `/health` 端点
- [ ] Dockerfile 配置正确
- [ ] docker-compose.yml 配置外部网络
- [ ] 容器名称（container_name）已设置
- [ ] 端口映射正确
- [ ] 环境变量配置完整
- [ ] services.yaml 配置已添加
- [ ] 路由映射正确
- [ ] 本地测试通过
- [ ] 日志输出正常
- [ ] 网络连接验证通过

## 附录

### A. 相关文档

- [API Gateway 配置化改造技术规范](../api-gateway-配置化改造-技术规范.md)
- [开发指南](./development-guide.md)
- [生产环境部署指南](../deployment/production-guide.md)
- [API 参考文档](../api/api-reference.md)

### B. 技术支持

如有问题，请联系：
- 技术支持邮箱：support@example.com
- 项目 Issue：https://github.com/your-org/api-gateway/issues

### C. 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-01-31 | 初始版本 |
