# 数据库安装指南（Windows）

本指南将帮助您在 Windows 上快速安装开发所需的数据库。

## 快速安装步骤

### 方案 1：推荐 - 使用 Chocolatey 包管理器（最简单）

如果您安装了 Chocolatey，可以一键安装所有数据库：

```powershell
# 以管理员权限打开 PowerShell，然后运行：
choco install postgresql mongodb redis-64 -y
```

### 方案 2：手动安装（适合大多数用户）

#### 1. 安装 PostgreSQL 15+

**下载地址**: https://www.postgresql.org/download/windows/
**推荐**: 使用 EnterpriseDB 安装器

**安装步骤**:
1. 下载并运行安装器
2. 安装时记住设置的密码（例如：`postgres`）
3. 端口保持默认：`5432`
4. 安装完成后，PostgreSQL 服务会自动启动

**创建项目数据库**:
```bash
# 打开 psql（开始菜单搜索 "SQL Shell"）
# 输入密码后执行：
CREATE DATABASE quant_platform;
CREATE USER quant_user WITH PASSWORD 'quant_password_dev';
GRANT ALL PRIVILEGES ON DATABASE quant_platform TO quant_user;
\q
```

#### 2. 安装 MongoDB 7.0+

**下载地址**: https://www.mongodb.com/try/download/community
**选择**: Windows x64, MSI 安装包

**安装步骤**:
1. 下载并运行安装器
2. 选择 "Complete" 完整安装
3. 勾选 "Install MongoDB as a Service"（作为服务安装）
4. 勾选 "Install MongoDB Compass"（图形化管理工具）
5. 安装完成后，MongoDB 服务会自动启动

**验证安装**:
```bash
# 打开命令行执行：
mongosh
# 如果能连接上说明安装成功，输入 exit 退出
```

#### 3. 安装 Redis 7.0+

**下载地址**: https://github.com/tporadowski/redis/releases
**选择**: Redis-x64-*.msi 最新版本

**安装步骤**:
1. 下载并运行安装器
2. 保持默认配置
3. 勾选 "Add Redis to PATH"
4. 勾选 "Install as Windows Service"
5. 安装完成后，Redis 服务会自动启动

**验证安装**:
```bash
# 打开命令行执行：
redis-cli ping
# 如果返回 PONG 说明安装成功
```

### 方案 3：最小化安装（仅核心功能）

如果您只想先体验核心功能，可以只安装 PostgreSQL：

1. 安装 PostgreSQL（必需）- 用于用户认证和基础数据
2. MongoDB 和 Redis 可以暂时跳过，我们会修改代码使其可选

## 验证所有服务

安装完成后，运行检查脚本：

```bash
cd d:\code\stock
scripts\check-services.bat
```

应该看到所有服务都显示 `[√] 服务运行中`。

## 服务管理

### 启动/停止服务

**使用 Windows 服务管理器**:
```bash
# 打开服务管理器
services.msc

# 找到以下服务：
# - postgresql-x64-15
# - MongoDB
# - Redis

# 右键可以启动/停止/重启服务
```

**使用命令行**:
```bash
# 启动服务
net start postgresql-x64-15
net start MongoDB
net start Redis

# 停止服务
net stop postgresql-x64-15
net stop MongoDB
net stop Redis
```

## 故障排查

### PostgreSQL 连接失败
- 检查服务是否运行：`services.msc`
- 检查端口是否被占用：`netstat -ano | findstr :5432`
- 查看日志：`C:\Program Files\PostgreSQL\15\data\pg_log\`

### MongoDB 连接失败
- 检查服务是否运行：`services.msc`
- 尝试手动启动：`mongod --dbpath C:\data\db`
- 查看日志：`C:\Program Files\MongoDB\Server\7.0\log\`

### Redis 连接失败
- 检查服务是否运行：`services.msc`
- 尝试手动启动：`redis-server`
- 默认无密码，如果设置了密码需要配置

## 下一步

完成数据库安装后，运行：

```bash
# 检查服务状态
scripts\check-services.bat

# 如果所有服务都正常，继续设置后端环境
```

## 需要帮助？

如果遇到问题：
1. 查看上述故障排查部分
2. 检查防火墙是否阻止了数据库端口
3. 确认 Windows 用户权限足够（建议使用管理员权限安装）
