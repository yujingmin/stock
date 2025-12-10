# 快速启动指南

本指南将帮助你快速启动个人量化投资平台的开发环境。

## 前置要求

确保你的系统已安装以下软件：

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.0+
- [Git](https://git-scm.com/)

可选（用于本地开发）：
- [Node.js](https://nodejs.org/) 20+
- [Python](https://www.python.org/) 3.11+

## 快速启动步骤

### 1. 克隆项目（如果尚未克隆）

```bash
git clone <repository-url>
cd stock
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件（可选，开发环境使用默认值即可）
# Windows: notepad .env
# macOS/Linux: nano .env
```

开发环境可以保持默认配置，生产环境需要修改所有密码和密钥。

### 3. 启动所有服务

```bash
# 启动所有服务（后台运行）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看服务日志
docker-compose logs -f
```

### 4. 等待服务启动

首次启动需要下载镜像和安装依赖，可能需要 5-10 分钟。你可以通过以下命令查看启动进度：

```bash
# 查看后端服务日志
docker-compose logs -f backend

# 查看前端服务日志
docker-compose logs -f frontend
```

### 5. 访问服务

服务启动完成后，可以通过以下地址访问：

| 服务 | 地址 | 说明 |
|-----|------|------|
| 前端应用 | http://localhost:3000 | React Web 应用 |
| 后端 API | http://localhost:8000 | FastAPI 后端服务 |
| API 文档 | http://localhost:8000/api/docs | Swagger UI 文档 |
| ReDoc 文档 | http://localhost:8000/api/redoc | ReDoc 风格文档 |
| PostgreSQL | localhost:5432 | 用户数据库 |
| MongoDB | localhost:27017 | 策略代码数据库 |
| Redis | localhost:6379 | 缓存与队列 |
| InfluxDB | http://localhost:8086 | 时序数据库 |

### 6. 验证服务运行状态

打开浏览器访问：

1. **前端首页**: http://localhost:3000
   - 应该显示 "欢迎使用量化投资平台"

2. **后端健康检查**: http://localhost:8000/health
   - 应该返回 `{"status": "healthy"}`

3. **API 文档**: http://localhost:8000/api/docs
   - 应该显示 Swagger UI 界面

## 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启所有服务
docker-compose restart

# 停止并删除所有数据（慎用！）
docker-compose down -v

# 查看运行中的服务
docker-compose ps

# 查看服务日志
docker-compose logs -f [service-name]
```

### 单个服务操作

```bash
# 重启某个服务
docker-compose restart backend

# 查看某个服务的日志
docker-compose logs -f backend

# 进入某个服务的容器
docker-compose exec backend bash
docker-compose exec frontend sh

# 重新构建某个服务
docker-compose build backend
```

### 数据库操作

```bash
# 连接到 PostgreSQL
docker-compose exec postgres psql -U quant_user -d quant_platform

# 连接到 MongoDB
docker-compose exec mongodb mongosh -u quant_user -p quant_password_dev

# 连接到 Redis
docker-compose exec redis redis-cli -a quant_password_dev
```

## 本地开发（不使用 Docker）

如果你想在本地直接运行服务进行开发：

### 后端本地开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端本地开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

注意：本地开发时仍需要启动数据库服务：

```bash
# 只启动数据库服务
docker-compose up -d postgres mongodb redis influxdb
```

## 故障排查

### 端口冲突

如果遇到端口被占用的错误，可以修改 `docker-compose.yml` 中的端口映射：

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # 将本地端口改为 8001
```

### 服务启动失败

1. 查看服务日志找出错误原因：
   ```bash
   docker-compose logs [service-name]
   ```

2. 尝试重新构建服务：
   ```bash
   docker-compose build --no-cache [service-name]
   docker-compose up -d
   ```

3. 清理并重新启动：
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### 数据库连接失败

1. 确认数据库服务正在运行：
   ```bash
   docker-compose ps
   ```

2. 检查健康状态：
   ```bash
   docker-compose ps
   ```
   所有服务的 STATUS 应该是 "Up (healthy)"

3. 等待数据库完全启动后再启动应用服务：
   ```bash
   # 先启动数据库
   docker-compose up -d postgres mongodb redis influxdb
   # 等待 30 秒
   sleep 30
   # 再启动应用服务
   docker-compose up -d backend frontend celery_worker
   ```

### 前端依赖安装失败

如果在国内网络环境下 npm 安装很慢，可以使用国内镜像：

```bash
cd frontend
npm install --registry=https://registry.npmmirror.com
```

## 下一步

服务启动成功后，你可以：

1. 阅读 [README.md](README.md) 了解项目架构
2. 查看 [openspec/changes/add-quant-platform/proposal.md](openspec/changes/add-quant-platform/proposal.md) 了解功能规划
3. 开始开发用户认证模块（Phase 1）
4. 访问 API 文档学习接口使用方法

## 获取帮助

如果遇到问题：

1. 查看服务日志：`docker-compose logs -f`
2. 检查 GitHub Issues
3. 查阅 Docker 和相关技术的官方文档

祝你开发顺利！
