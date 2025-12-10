# 个人量化投资平台

集"数据获取-策略开发-回测优化-风控管理-实时通知"于一体的个人量化投资平台（网页版）。

## 项目特性

- 🔄 **市场数据服务**：多市场实时行情接入、财务报表、因子数据统一管理
- 💻 **策略开发环境**：集成 Jupyter 交互式编辑器、Backtrader 回测框架、代码版本管理
- 📊 **回测与优化系统**：真实交易参数配置、参数优化、实盘级模拟交易
- 🛡️ **风险控制模块**：账户级与策略级风控规则、实时监控与预警
- 📱 **消息通知系统**：微信小程序推送、结构化消息、个性化规则配置
- 🔐 **数据安全保障**：双重加密存储、HTTPS 传输、本地备份导出

## 技术栈

### 前端
- React 18 + TypeScript
- Ant Design 5 (UI 组件库)
- Zustand (状态管理)
- ECharts (数据可视化)
- Monaco Editor (代码编辑器)
- Vite (构建工具)

### 后端
- Python 3.11
- FastAPI (Web 框架)
- SQLAlchemy (ORM)
- Celery (异步任务队列)
- Backtrader (回测框架)
- akshare (数据源)

### 数据库
- PostgreSQL (关系型数据)
- MongoDB (文档型数据)
- Redis (缓存与队列)
- InfluxDB (时序数据)

## 项目结构

```
.
├── backend/              # 后端应用
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # 数据模型
│   │   ├── schemas/     # Pydantic 模式
│   │   ├── services/    # 业务逻辑
│   │   ├── tasks/       # Celery 任务
│   │   └── utils/       # 工具函数
│   ├── tests/           # 测试文件
│   ├── Dockerfile       # 生产环境镜像
│   ├── Dockerfile.dev   # 开发环境镜像
│   └── requirements.txt # Python 依赖
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── api/        # API 客户端
│   │   ├── components/ # 组件
│   │   ├── hooks/      # 自定义 Hooks
│   │   ├── layouts/    # 布局组件
│   │   ├── pages/      # 页面组件
│   │   ├── routes/     # 路由配置
│   │   ├── store/      # 状态管理
│   │   ├── types/      # TypeScript 类型
│   │   └── utils/      # 工具函数
│   ├── public/         # 静态资源
│   ├── Dockerfile      # 生产环境镜像
│   ├── Dockerfile.dev  # 开发环境镜像
│   └── package.json    # Node 依赖
├── nginx/              # Nginx 配置
│   ├── nginx.conf      # Nginx 配置文件
│   └── ssl/            # SSL 证书目录
├── openspec/           # OpenSpec 变更管理
│   └── changes/        # 变更提案
├── docker-compose.yml       # 开发环境编排
├── docker-compose.prod.yml  # 生产环境编排
└── .env.example        # 环境变量示例
```

## 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Node.js 20+ (本地开发)
- Python 3.11+ (本地开发)

### 开发环境部署

1. 克隆项目

```bash
git clone <repository-url>
cd stock
```

2. 复制环境变量文件

```bash
cp .env.example .env
# 编辑 .env 文件，填写必要的配置
```

3. 启动开发环境

```bash
docker-compose up -d
```

服务访问地址：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/api/docs
- PostgreSQL：localhost:5432
- MongoDB：localhost:27017
- Redis：localhost:6379
- InfluxDB：http://localhost:8086

### 生产环境部署

1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置生产环境密钥和密码
```

2. 配置 SSL 证书

将 SSL 证书文件放置到 `nginx/ssl/` 目录：
- cert.pem
- key.pem

3. 构建并启动服务

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

4. 配置域名解析

将域名 A 记录指向服务器 IP 地址。

### 本地开发

#### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn app.main:app --reload
```

#### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 开发指南

### 代码规范

- 后端代码遵循 PEP 8 规范，使用 black 格式化
- 前端代码使用 ESLint + Prettier 进行检查和格式化
- 提交前运行代码检查：

```bash
# 后端
cd backend
black app/
flake8 app/

# 前端
cd frontend
npm run lint
npm run format
```

### 测试

```bash
# 后端测试
cd backend
pytest

# 前端测试（待配置）
cd frontend
npm test
```

## 功能模块

### 1. 市场数据服务
- 实时行情数据接入
- 财务报表与宏观经济数据
- 量化因子计算
- 数据可视化（K线图、热力图）

### 2. 策略开发环境
- Monaco Editor 代码编辑器
- Jupyter Kernel 集成
- 策略版本管理
- 代码片段库

### 3. 回测与优化系统
- Backtrader 回测引擎
- 真实交易参数配置
- 参数优化（网格搜索、遗传算法）
- 实盘级模拟交易

### 4. 风险控制模块
- 账户级风控规则
- 策略级止损止盈
- 实时风险监控
- 压力测试

### 5. 消息通知系统
- 微信小程序推送
- 持仓关联触发
- 消息优先级管理
- 通知中心

### 6. 用户认证与账户管理
- 手机验证码登录
- JWT 令牌认证
- 多策略管理
- 数据加密存储

## 数据安全

- 全站 HTTPS 加密传输
- 策略代码 AES-256 加密存储
- 用户密码 bcrypt 哈希
- 敏感数据双重加密
- 本地备份导出支持

## 许可证

本项目仅供个人学习和使用，未经许可不得用于商业用途。

## 联系方式

如有问题或建议，请提交 Issue。
