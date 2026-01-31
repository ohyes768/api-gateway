# API Gateway

通用 API 网关，提供统一入口，通过配置文件动态路由转发到后端微服务。

## 功能特性

- ✅ 统一 API 入口
- ✅ **配置文件驱动的服务管理**（YAML）
- ✅ **动态路由注册**（无需修改代码）
- ✅ 启动时服务可达性验证
- ✅ 健康检查端点
- ✅ 统一异常处理
- ✅ 结构化日志
- ✅ Docker 部署

## 技术栈

- Python 3.10+
- FastAPI 0.104+
- Uvicorn
- HTTPX
- Pydantic
- PyYAML

## 项目结构

```
api-gateway/
├── config/
│   ├── services.yaml        # 服务配置文件（核心）
│   └── services.yaml.example # 配置文件示例
├── src/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置加载和验证
│   ├── models/              # 数据模型
│   │   ├── __init__.py
│   │   └── service_config.py # 服务配置模型
│   ├── routes/              # 路由模块
│   │   └── health.py        # 健康检查路由
│   └── utils/               # 工具模块
│       ├── logger.py        # 日志工具
│       ├── proxy.py         # 代理工具
│       └── dynamic_router.py # 动态路由注册器
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 快速开始

### 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 创建配置文件
cp config/services.yaml.example config/services.yaml
# 编辑 config/services.yaml，配置后端服务

# 3. 启动服务
python src/main.py
```

### Docker 部署

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

## 配置说明

### 服务配置文件 `config/services.yaml`

```yaml
services:
  # 服务名称（唯一标识）
  news_analysis:
    url: http://news-analysis-service:8030  # 后端服务地址
    enabled: true                            # 是否启用
    health_path: /health                     # 健康检查路径
    routes:                                  # 路由配置列表
      - path: /api/news-analysis             # 网关对外暴露的路径
        method: POST                         # HTTP 方法
        backend_path: /api/analyze           # 后端服务路径（可选）
```

### 环境变量配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `LOG_LEVEL` | 日志级别 | INFO |
| `TIMEOUT` | 请求超时时间（秒） | 30 |

## 添加新服务（无需修改代码）

**仅需三步，添加新服务：**

1. **编辑配置文件** `config/services.yaml`：

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
      - path: /api/webhook/production
        method: POST
        backend_path: /webhook/prod
```

2. **重启网关服务**：

```bash
docker-compose restart api-gateway
```

3. **验证新服务**：

```bash
curl http://localhost:8010/api/webhook/test
```

**完成！** 无需编写任何代码，网关自动注册新路由。

## API 端点

### 健康检查

```http
GET /health
```

### 其他端点

所有业务端点由 `config/services.yaml` 配置文件定义。

**当前配置的端点：**

- `POST /api/news-analysis` - 新闻分析
- `GET /api/a-stock` - A股新股信息
- `GET /api/hk-stock` - 港股新股信息

## 配置文件详解

### 服务配置项

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `url` | string | 是 | 后端服务地址（需包含协议） |
| `enabled` | boolean | 否 | 是否启用服务，默认 `true` |
| `health_path` | string | 否 | 健康检查路径，默认 `/health` |
| `routes` | array | 是 | 路由配置列表 |

### 路由配置项

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `path` | string | 是 | 网关对外暴露的路径 |
| `method` | string | 否 | HTTP 方法，默认 `GET` |
| `backend_path` | string | 否 | 后端服务路径，默认等于 `path` |

### 支持的 HTTP 方法

- `GET`
- `POST`
- `PUT`
- `DELETE`
- `PATCH`

## 版本历史

### v2.1.0 (当前版本)
- ✅ **完全配置化改造** - 通过 YAML 配置文件管理所有服务
- ✅ **动态路由注册** - 启动时根据配置自动注册路由
- ✅ **启动时验证** - 验证配置文件格式和服务可达性
- ✅ **服务启用/禁用** - 支持通过配置控制服务状态
- ✅ **零代码添加服务** - 添加新服务无需修改代码

### v2.0.0
- ✅ 从 new-index-info 项目剥离
- ✅ 模块化路由
- ✅ 统一代理工具
- ✅ 改进配置管理
- ✅ 添加新闻分析路由

## 许可证

MIT
