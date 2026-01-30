# 部署指南

## 目录

- [环境要求](#环境要求)
- [本地开发部署](#本地开发部署)
- [Docker 部署](#docker-部署)
- [生产环境部署](#生产环境部署)
- [环境变量配置](#环境变量配置)
- [监控和日志](#监控和日志)
- [故障排查](#故障排查)

---

## 环境要求

### 本地开发

- **Python**: 3.10 或更高版本
- **包管理器**: uv
- **操作系统**: Windows / Linux / macOS

### Docker 部署

- **Docker**: 20.10 或更高版本
- **Docker Compose**: 2.0 或更高版本

### 生产环境

- **服务器**: Linux (推荐 Ubuntu 20.04+)
- **内存**: 最小 512MB，推荐 1GB+
- **CPU**: 最小 1 核，推荐 2 核+
- **网络**: 需要访问后端微服务

---

## 本地开发部署

### 1. 安装 uv

如果尚未安装 uv：

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 创建虚拟环境

```bash
uv venv .venv
```

### 3. 激活虚拟环境

**Windows**:
```bash
.venv\Scripts\activate
```

**Linux / macOS**:
```bash
source .venv/bin/activate
```

### 4. 安装依赖

```bash
uv pip install -r requirements.txt
```

### 5. 配置环境变量

复制环境变量示例文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置后端服务地址：

```env
LOG_LEVEL=INFO
TIMEOUT=30

A_STOCK_SERVICE_URL=http://localhost:8001
HK_STOCK_SERVICE_URL=http://localhost:8002
NEWS_ANALYSIS_SERVICE_URL=http://localhost:8030
```

### 6. 启动服务

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8010 --reload
```

服务将在 `http://localhost:8010` 启动。

---

## Docker 部署

### 单独构建镜像

```bash
docker build -t api-gateway:latest .
```

### 运行容器

```bash
docker run -d \
  --name api-gateway \
  -p 8010:8000 \
  -e A_STOCK_SERVICE_URL=http://a-stock-service:8001 \
  -e HK_STOCK_SERVICE_URL=http://hk-stock-service:8002 \
  -e NEWS_ANALYSIS_SERVICE_URL=http://news-analysis-service:8030 \
  api-gateway:latest
```

### 使用 Docker Compose

**1. 启动服务**:

```bash
docker-compose up -d
```

**2. 查看日志**:

```bash
docker-compose logs -f api-gateway
```

**3. 停止服务**:

```bash
docker-compose down
```

**4. 重启服务**:

```bash
docker-compose restart api-gateway
```

---

## 生产环境部署

### 方案一：Docker Compose（推荐）

#### 1. 准备配置文件

创建生产环境配置 `.env.production`:

```env
LOG_LEVEL=WARNING
TIMEOUT=60

A_STOCK_SERVICE_URL=http://a-stock-service:8001
HK_STOCK_SERVICE_URL=http://hk-stock-service:8002
NEWS_ANALYSIS_SERVICE_URL=http://news-analysis-service:8030
```

#### 2. 使用生产配置启动

```bash
docker-compose --env-file .env.production up -d
```

#### 3. 配置反向代理（Nginx）

创建 Nginx 配置文件 `/etc/nginx/sites-available/api-gateway`:

```nginx
upstream api_gateway {
    server localhost:8010;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://api_gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/api-gateway /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 4. 配置 SSL（可选）

使用 Let's Encrypt 免费证书：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
```

### 方案二：Kubernetes 部署

#### 1. 创建 Deployment

`k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: api-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: LOG_LEVEL
          value: "WARNING"
        - name: TIMEOUT
          value: "60"
        - name: A_STOCK_SERVICE_URL
          value: "http://a-stock-service:8001"
        - name: HK_STOCK_SERVICE_URL
          value: "http://hk-stock-service:8002"
        - name: NEWS_ANALYSIS_SERVICE_URL
          value: "http://news-analysis-service:8030"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 2. 创建 Service

`k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
spec:
  selector:
    app: api-gateway
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### 3. 部署

```bash
kubectl apply -f k8s/
```

### 方案三：Systemd 服务（本地服务器）

#### 1. 创建服务文件

`/etc/systemd/system/api-gateway.service`:

```ini
[Unit]
Description=API Gateway Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/api-gateway
Environment="PATH=/opt/api-gateway/.venv/bin"
ExecStart=/opt/api-gateway/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8010
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable api-gateway
sudo systemctl start api-gateway
```

#### 3. 查看状态

```bash
sudo systemctl status api-gateway
```

---

## 环境变量配置

### 配置项说明

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| LOG_LEVEL | 否 | INFO | 日志级别：DEBUG, INFO, WARNING, ERROR |
| TIMEOUT | 否 | 30 | 请求超时时间（秒） |
| A_STOCK_SERVICE_URL | 是 | http://a-stock-service:8001 | A股服务地址 |
| HK_STOCK_SERVICE_URL | 是 | http://hk-stock-service:8002 | 港股服务地址 |
| NEWS_ANALYSIS_SERVICE_URL | 是 | http://news-analysis-service:8030 | 新闻分析服务地址 |

### 配置建议

**开发环境**:
```env
LOG_LEVEL=DEBUG
TIMEOUT=30
```

**生产环境**:
```env
LOG_LEVEL=WARNING
TIMEOUT=60
```

---

## 监控和日志

### 健康检查

Gateway 提供健康检查端点：

```bash
curl http://localhost:8010/health
```

**健康检查配置**:

- Docker Compose 自动健康检查：每 30 秒检查一次
- Kubernetes Liveness/Readiness Probe
- 监控系统可定期调用该端点

### 日志管理

**Docker 日志**:

```bash
# 查看实时日志
docker-compose logs -f api-gateway

# 查看最近 100 行
docker-compose logs --tail=100 api-gateway
```

**Systemd 日志**:

```bash
journalctl -u api-gateway -f
```

**Kubernetes 日志**:

```bash
kubectl logs -f deployment/api-gateway
```

### 性能监控

建议集成以下监控工具：

1. **Prometheus + Grafana**: 收集和可视化性能指标
2. **ELK Stack**: 集中日志管理
3. **Sentry**: 错误追踪和报警

---

## 故障排查

### 常见问题

#### 1. 服务无法启动

**检查端口占用**:

```bash
# Linux / macOS
lsof -i :8010

# Windows
netstat -ano | findstr :8010
```

**检查日志**:

```bash
docker-compose logs api-gateway
```

#### 2. 请求超时

**原因**:
- 后端服务未启动或不可达
- 网络连接问题
- 超时时间配置过短

**解决方案**:

1. 检查后端服务状态
2. 增加 `TIMEOUT` 环境变量值
3. 检查网络连通性

```bash
# 测试后端服务连接
curl http://a-stock-service:8001/api/stocks
```

#### 3. 503 Service Unavailable

**原因**:
- 后端服务 URL 配置错误
- 后端服务崩溃
- 网络分区

**解决方案**:

1. 验证环境变量配置
2. 检查后端服务日志
3. 测试网络连接

#### 4. 高 CPU/内存占用

**原因**:
- 请求量过大
- 内存泄漏
- 并发连接过多

**解决方案**:

1. 增加服务器资源
2. 配置负载均衡（多实例）
3. 添加速率限制
4. 优化后端服务调用

### 调试模式

启用调试日志：

```env
LOG_LEVEL=DEBUG
```

重启服务后查看详细日志。

---

## 性能优化建议

### 1. 连接池优化

HTTPX 默认使用连接池，无需额外配置。

### 2. 缓存策略

对于频繁访问的数据，可考虑添加缓存层（Redis）。

### 3. 负载均衡

部署多个 Gateway 实例，使用 Nginx 或云负载均衡器分发请求。

### 4. 资源限制

Docker Compose 添加资源限制：

```yaml
services:
  api-gateway:
    # ...
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

---

## 安全建议

1. **限制访问**: 使用防火墙限制 API 访问来源
2. **HTTPS**: 生产环境必须使用 HTTPS
3. **认证授权**: 添加 API Key 或 JWT 认证
4. **速率限制**: 防止 DDoS 攻击
5. **日志脱敏**: 避免记录敏感信息
6. **定期更新**: 及时更新依赖包和基础镜像

---

## 备份和恢复

### 配置备份

备份 `.env` 文件和 Nginx 配置：

```bash
tar -czf api-gateway-config-backup-$(date +%Y%m%d).tar.gz \
  .env /etc/nginx/sites-available/api-gateway
```

### 数据备份

Gateway 无状态，无需数据备份。重点备份配置文件。

---

## 更新和升级

### Docker 版本更新

```bash
docker-compose pull
docker-compose up -d
```

### 源码更新

```bash
git pull
docker-compose build
docker-compose up -d
```

### 回滚

```bash
git checkout <previous-tag>
docker-compose build
docker-compose up -d
```

---

## 联系支持

如遇到部署问题，请查看：

1. GitHub Issues: https://github.com/your-repo/issues
2. 项目文档: `/docs` 目录
3. 日志文件: 查看服务日志获取详细错误信息
