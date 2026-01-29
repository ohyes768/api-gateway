# API Gateway

通用 API 网关，提供统一入口，路由转发到后端微服务。

## 功能特性

- ✅ 统一 API 入口
- ✅ 路由转发到后端微服务
- ✅ 健康检查端点
- ✅ 统一异常处理
- ✅ 结构化日志
- ✅ Docker 部署

## 技术栈

- Python 3.10
- FastAPI 0.104
- Uvicorn
- HTTPX
- Pydantic

## 项目结构

```
api-gateway/
├── src/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 配置管理
│   ├── routes/              # 路由模块
│   │   ├── health.py        # 健康检查
│   │   ├── a_stock.py       # A股新股信息路由
│   │   ├── hk_stock.py      # 港股新股信息路由
│   │   └── news_analysis.py # 新闻分析路由
│   └── utils/               # 工具模块
│       ├── logger.py        # 日志工具
│       └── proxy.py         # 代理工具
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

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置后端服务 URL

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

## API 端点

### 健康检查

```http
GET /health
```

### A股新股信息

```http
GET /api/a-stock
```

### 港股新股信息

```http
GET /api/hk-stock
```

### 新闻分析

```http
POST /api/news-analysis
Content-Type: application/json

{
  "text": "新闻文本内容"
}
```

## 配置说明

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `LOG_LEVEL` | 日志级别 | INFO |
| `TIMEOUT` | 请求超时时间（秒） | 30 |
| `A_STOCK_SERVICE_URL` | A股服务地址 | http://a-stock-service:8001 |
| `HK_STOCK_SERVICE_URL` | 港股服务地址 | http://hk-stock-service:8002 |
| `NEWS_ANALYSIS_SERVICE_URL` | 新闻分析服务地址 | http://news-analysis-service:8030 |

## 版本历史

### v2.0.0
- ✅ 从 new-index-info 项目剥离
- ✅ 模块化路由
- ✅ 统一代理工具
- ✅ 改进配置管理
- ✅ 添加新闻分析路由

## 许可证

MIT
