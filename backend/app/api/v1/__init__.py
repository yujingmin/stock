"""
API v1 路由汇总
"""
from fastapi import APIRouter

from app.api.v1.endpoints import market_data, backtesting, notification, notification_rule

api_router = APIRouter()

# 注册路由
api_router.include_router(market_data.router, prefix="/market-data", tags=["市场数据"])
api_router.include_router(backtesting.router, prefix="/backtesting", tags=["回测系统"])
api_router.include_router(notification.router, prefix="/notification", tags=["消息通知"])
api_router.include_router(notification_rule.router, prefix="/notification-rule", tags=["推送规则"])
# api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
# api_router.include_router(strategy.router, prefix="/strategy", tags=["策略开发"])
# api_router.include_router(risk.router, prefix="/risk", tags=["风险控制"])


@api_router.get("/")
async def api_root():
    """API 根路径"""
    return {
        "message": "量化投资平台 API v1",
        "endpoints": {
            "docs": "/api/docs",
            "redoc": "/api/redoc",
            "openapi": "/api/openapi.json",
        },
    }
