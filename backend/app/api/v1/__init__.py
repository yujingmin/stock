"""
API v1 路由汇总
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, market_data, strategy
# from app.api.v1.endpoints import backtesting, notification, notification_rule

api_router = APIRouter()

# 认证路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 市场数据路由
api_router.include_router(market_data.router, prefix="/market-data", tags=["市场数据"])

# 策略开发路由
api_router.include_router(strategy.router, prefix="/strategy", tags=["策略开发"])

# 临时注释掉具体路由，等服务层实现后再启用
# api_router.include_router(backtesting.router, prefix="/backtesting", tags=["回测系统"])
# api_router.include_router(notification.router, prefix="/notification", tags=["消息通知"])
# api_router.include_router(notification_rule.router, prefix="/notification-rule", tags=["推送规则"])
# api_router.include_router(strategy.router, prefix="/strategy", tags=["策略开发"])
# api_router.include_router(risk.router, prefix="/risk", tags=["风险控制"])


@api_router.get("/")
async def api_root():
    """API 根路径"""
    return {
        "message": "量化投资平台 API v1",
        "status": "开发中 - 服务层待实现",
        "endpoints": {
            "docs": "/api/docs",
            "redoc": "/api/redoc",
            "openapi": "/api/openapi.json",
        },
    }


@api_router.get("/status")
async def api_status():
    """API 状态检查"""
    return {
        "api_version": "v1",
        "database": "PostgreSQL - 已连接",
        "mongodb": "未启用",
        "redis": "未启用",
        "influxdb": "未启用",
    }
