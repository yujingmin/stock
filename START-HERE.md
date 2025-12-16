# 快速启动指南（本地开发模式）

## 当前进度

✅ **已完成**:
1. Python 3.13.9 和 Node.js v24.11.1 已安装
2. 后端配置文件已创建 ([backend/.env](backend/.env))
3. 前端配置文件已创建 ([frontend/.env](frontend/.env))
4. 代码已修改，MongoDB/Redis/InfluxDB 为可选
5. Python 依赖正在安装中...

⏳ **待完成**:
1. 安装 PostgreSQL 数据库
2. 创建数据库和用户
3. 启动后端服务
4. 启动前端服务

---

## 步骤 1: 安装 PostgreSQL（进行中）

您正在下载 PostgreSQL，安装时请注意：

### 安装配置
- **端口**: 保持默认 `5432`
- **密码**: 记住您设置的密码（建议: `postgres`）
- **语言**: English（避免中文路径问题）

### 安装后操作

安装完成后，运行数据库初始化脚本：

```bash
# 方式1: 使用提供的脚本（推荐）
scripts\init-postgres.bat

# 方式2: 手动创建（在 SQL Shell 中执行）
psql -U postgres
CREATE DATABASE quant_platform;
CREATE USER quant_user WITH PASSWORD 'quant_password_dev';
GRANT ALL PRIVILEGES ON DATABASE quant_platform TO quant_user;
ALTER USER quant_user WITH CREATEDB;
\q
```

---

## 步骤 2: 启动后端服务

PostgreSQL 安装完成后，启动后端：

```bash
# 使用快速启动脚本
scripts\start-backend.bat

# 或手动启动
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**预期输出**:
```
⊗ MongoDB 已禁用
⊗ Redis 已禁用
⊗ InfluxDB 已禁用
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

验证后端：打开 http://localhost:8000/api/docs

---

## 步骤 3: 启动前端服务

在新的命令行窗口：

```bash
# 使用快速启动脚本
scripts\start-frontend.bat

# 或手动启动
cd frontend
npm run dev
```

**预期输出**:
```
VITE v5.0.11  ready in 1234 ms
➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

访问前端：http://localhost:3000

---

## 步骤 4: 验证服务

### 检查清单

1. **后端 API**: http://localhost:8000/health
   - 应返回: `{"status": "healthy"}`

2. **API 文档**: http://localhost:8000/api/docs
   - 应显示 Swagger UI 界面

3. **前端应用**: http://localhost:3000
   - 应显示欢迎页面

---

## 常见问题

### 后端启动失败

**问题**: `asyncpg.exceptions.InvalidCatalogNameError: database "quant_platform" does not exist`

**解决**: 运行 `scripts\init-postgres.bat` 创建数据库

---

**问题**: `Connection refused [Errno 10061]`

**解决**: 确认 PostgreSQL 服务正在运行
```bash
# 检查服务
services.msc
# 找到 postgresql-x64-15，确认状态为"正在运行"
```

---

### 前端启动失败

**问题**: `Error: Cannot find module...`

**解决**: 重新安装依赖
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --registry=https://registry.npmmirror.com
```

---

## 下一步开发

服务启动成功后，您可以：

1. **查看 API 文档**: http://localhost:8000/api/docs
   - 测试市场数据 API
   - 测试回测系统 API

2. **开始前端开发**:
   - 修改代码会自动热重载
   - 查看 [frontend/src](frontend/src) 目录

3. **后续安装数据库**（可选）:
   - MongoDB - 用于策略代码存储
   - Redis - 用于缓存和任务队列
   - InfluxDB - 用于时序行情数据

   安装后修改 [backend/.env](backend/.env):
   ```env
   MONGODB_ENABLED=true
   REDIS_ENABLED=true
   INFLUXDB_ENABLED=true
   ```

---

## 需要帮助？

如果遇到问题，请：
1. 检查 PostgreSQL 是否安装并运行
2. 查看后端日志输出的错误信息
3. 运行 `scripts\check-services.bat` 检查服务状态

祝开发顺利！🚀
