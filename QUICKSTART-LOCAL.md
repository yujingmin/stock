# 本地开发启动指南（不使用 Docker）

本指南适用于无法使用 Docker 的环境。

## 前置要求

请确保已安装：
- **Python 3.11+**：https://www.python.org/downloads/
- **Node.js 20+**：https://nodejs.org/
- **PostgreSQL 15+**：https://www.postgresql.org/download/windows/
- **MongoDB 7.0+**：https://www.mongodb.com/try/download/community
- **Redis 7.0+**：https://github.com/tporadowski/redis/releases（Windows 版）

## 快速启动步骤

### 1. 安装并启动数据库服务

#### PostgreSQL
```bash
# 安装后，创建数据库和用户
psql -U postgres
CREATE DATABASE quant_platform;
CREATE USER quant_user WITH PASSWORD 'quant_password_dev';
GRANT ALL PRIVILEGES ON DATABASE quant_platform TO quant_user;
```

#### MongoDB
```bash
# 启动 MongoDB（Windows 服务会自动启动）
# 或手动启动：
mongod --dbpath C:\data\db
```

#### Redis
```bash
# 启动 Redis（Windows 服务会自动启动）
# 或手动启动：
redis-server
```

### 2. 配置环境变量

创建 `backend/.env` 文件：
```env
DATABASE_URL=postgresql://quant_user:quant_password_dev@localhost:5432/quant_platform
MONGODB_URL=mongodb://localhost:27017/quant_platform
REDIS_URL=redis://localhost:6379/0
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_token_here
INFLUXDB_ORG=quant_platform
INFLUXDB_BUCKET=market_data

# JWT 配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. 启动后端服务

```bash
cd backend

# 创建并激活虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 启动前端服务

打开新的命令行窗口：

```bash
cd frontend

# 安装依赖（使用国内镜像）
npm install --registry=https://registry.npmmirror.com

# 启动开发服务器
npm run dev
```

### 5. 访问应用

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/api/docs

## 常见问题

### Python 依赖安装失败

使用清华镜像源：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Node.js 依赖安装慢

使用淘宝镜像：
```bash
npm install --registry=https://registry.npmmirror.com
```

### PostgreSQL 连接失败

检查 PostgreSQL 服务是否运行：
```bash
# Windows 服务管理
services.msc
# 找到 postgresql-x64-15 服务，确保已启动
```

### InfluxDB 暂时不可用

如果暂时不需要时序数据功能，可以在代码中跳过 InfluxDB 连接检查。
