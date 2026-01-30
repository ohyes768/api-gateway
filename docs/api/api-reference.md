# API 接口文档

## 概述

API Gateway 提供统一的 RESTful API 接口，作为所有后端微服务的统一入口。所有请求由 Gateway 接收后，根据路由规则转发到相应的后端服务。

**基础 URL**: `http://localhost:8010` (本地) 或 `http://your-server:8010` (生产环境)

**响应格式**: 所有接口返回 JSON 格式数据

---

## 目录

- [健康检查](#健康检查)
- [A股新股信息](#a股新股信息)
- [港股新股信息](#港股新股信息)
- [新闻分析](#新闻分析)
- [错误码说明](#错误码说明)

---

## 健康检查

### GET /health

检查 API Gateway 服务的健康状态。

**请求示例**:
```bash
curl http://localhost:8010/health
```

**响应示例**:
```json
{
  "status": "ok",
  "service": "api-gateway",
  "version": "2.0.0",
  "timestamp": "2025-01-30T12:34:56.789012"
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | 服务状态，`"ok"` 表示正常 |
| service | string | 服务名称 |
| version | string | 服务版本号 |
| timestamp | string | 当前时间（ISO 8601 格式） |

---

## A股新股信息

### GET /api/a-stock

获取 A股新股信息列表。Gateway 将请求转发到 `a-stock-service:8001` 后端服务。

**请求示例**:
```bash
curl http://localhost:8010/api/a-stock
```

**请求参数**: 无

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "stock_code": "301500",
      "stock_name": "示例股票",
      "issue_date": "2025-02-01",
      "price": 25.50,
      "volume": 50000000
    }
  ]
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 响应状态码 |
| message | string | 响应消息 |
| data | array | 股票信息列表（具体字段由后端服务决定） |

**转发路径**:
- Gateway: `GET /api/a-stock`
- 后端服务: `GET http://a-stock-service:8001/api/stocks`

---

## 港股新股信息

### GET /api/hk-stock

获取港股新股信息列表。Gateway 将请求转发到 `hk-stock-service:8002` 后端服务。

**请求示例**:
```bash
curl http://localhost:8010/api/hk-stock
```

**请求参数**: 无

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "stock_code": "01234",
      "stock_name": "示例港股",
      "ipo_date": "2025-02-01",
      "price_range": "10.50-12.50",
      "market_cap": 5000000000
    }
  ]
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 响应状态码 |
| message | string | 响应消息 |
| data | array | 股票信息列表（具体字段由后端服务决定） |

**转发路径**:
- Gateway: `GET /api/hk-stock`
- 后端服务: `GET http://hk-stock-service:8002/api/stocks`

---

## 新闻分析

### POST /api/news-analysis

对新闻文本进行智能分析。Gateway 将请求转发到 `news-analysis-service:8030` 后端服务。

**请求示例**:
```bash
curl -X POST http://localhost:8010/api/news-analysis \
  -H "Content-Type: application/json" \
  -d '{"text": "示例新闻文本内容"}'
```

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 待分析的新闻文本内容 |

**请求体示例**:
```json
{
  "text": "某公司发布新产品，预计将带来市场变革..."
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "sentiment": "positive",
    "keywords": ["产品", "市场", "变革"],
    "summary": "该新闻传达了积极的市场信号"
  }
}
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 响应状态码 |
| message | string | 响应消息 |
| data | object | 分析结果（具体字段由后端服务决定） |

**转发路径**:
- Gateway: `POST /api/news-analysis`
- 后端服务: `POST http://news-analysis-service:8030/api/analyze`

---

## 错误码说明

### HTTP 状态码

| 状态码 | 说明 | 示例场景 |
|--------|------|----------|
| 200 | 请求成功 | 正常返回数据 |
| 400 | 请求参数错误 | 不支持的 HTTP 方法 |
| 503 | 服务不可用 | 后端服务超时或连接失败 |
| 500 | 内部服务错误 | 未预期的服务器错误 |

### 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "detail": "错误描述信息"
}
```

**常见错误示例**:

```json
{
  "detail": "A股服务请求超时"
}
```

```json
{
  "detail": "新闻分析服务暂时不可用"
}
```

### 错误处理建议

1. **超时错误 (503)**: 检查后端服务是否正常运行
2. **服务不可用 (503)**: 检查后端服务网络连接
3. **参数错误 (400)**: 检查请求方法和参数格式
4. **内部错误 (500)**: 查看 Gateway 日志获取详细信息

---

## 附录

### 服务端点配置

Gateway 通过环境变量配置后端服务地址：

| 服务名 | 环境变量 | 默认值 | 端口 |
|--------|----------|--------|------|
| A股服务 | A_STOCK_SERVICE_URL | http://a-stock-service:8001 | 8001 |
| 港股服务 | HK_STOCK_SERVICE_URL | http://hk-stock-service:8002 | 8002 |
| 新闻分析服务 | NEWS_ANALYSIS_SERVICE_URL | http://news-analysis-service:8030 | 8030 |

### 超时配置

默认请求超时时间：**30 秒**

可通过环境变量 `TIMEOUT` 配置。

---

## 更新日志

### v2.0.0 (2025-01-30)
- 初始版本发布
- 支持健康检查、A股/港股新股信息、新闻分析三大接口
