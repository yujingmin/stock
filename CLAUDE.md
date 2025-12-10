<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md
请始终使用简体中文与我对话，并在回答时保持专业、简洁。

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

这是一个包含前后端的 Monorepo 项目：

- `backend/` - FastAPI 后端应用（Python 3.11）
  - `app/api/` - API 路由
  - `app/core/` - 核心配置（数据库、安全、配置）
  - `app/models/` - 数据模型
  - `app/services/` - 业务逻辑
  - `app/tasks/` - Celery 异步任务

- `frontend/` - React 前端应用（TypeScript + Vite）
  - `src/api/` - API 客户端
  - `src/components/` - 可复用组件
  - `src/pages/` - 页面组件
  - `src/store/` - Zustand 状态管理

- `nginx/` - Nginx 反向代理配置
- `openspec/` - OpenSpec 变更管理
- `docker-compose.yml` - 开发环境编排
- `docker-compose.prod.yml` - 生产环境编排

## Development Setup

### 快速启动

详见 [QUICKSTART.md](QUICKSTART.md)

```bash
# 启动开发环境
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 访问地址

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/api/docs

### 本地开发

**后端**：
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**前端**：
```bash
cd frontend
npm install
npm run dev
```

### 代码质量检查

**后端**：
```bash
cd backend
black app/          # 代码格式化
flake8 app/         # 代码检查
pytest              # 运行测试
```

**前端**：
```bash
cd frontend
npm run lint        # ESLint 检查
npm run format      # Prettier 格式化
```

## Architecture

### 技术栈

**前端**：
- React 18 + TypeScript
- Ant Design 5 (UI 组件)
- Zustand (状态管理)
- ECharts (数据可视化)
- Monaco Editor (代码编辑器)
- Vite (构建工具)

**后端**：
- FastAPI (Web 框架)
- SQLAlchemy (ORM)
- Celery + Redis (异步任务)
- Backtrader (回测框架)
- akshare (数据源)

**数据库**：
- PostgreSQL - 用户数据、策略配置、交易记录
- MongoDB - 策略代码、回测报告
- Redis - 缓存、会话、任务队列
- InfluxDB - 时序行情数据

### 架构模式

- **前后端分离**：前端通过 RESTful API 与后端通信
- **微服务化**：后端按业务领域拆分服务模块
- **异步任务**：耗时操作（回测）通过 Celery 异步执行
- **实时通信**：WebSocket 用于行情推送和策略信号

### 数据流

1. **实时行情**：交易所 → akshare → 数据服务 → InfluxDB → WebSocket → 前端
2. **策略开发**：用户编辑 → MongoDB（加密存储）→ 版本管理 → 回测引擎
3. **风控通知**：策略引擎 → 风控引擎 → 通知服务 → 微信小程序

### 认证与授权

- JWT 令牌认证（7天有效期）
- Redis 会话管理（30分钟无操作自动登出）
- 手机短信验证码 + 密码双重登录
- 异地登录预警

### 数据安全

- 全站 HTTPS 加密传输
- 策略代码 AES-256 加密存储
- 用户密码 bcrypt 哈希
- 敏感数据双重加密
