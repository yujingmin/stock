# Models 初始化文件
"""
导入所有模型以便于使用
"""

# PostgreSQL 模型
from app.models.user import User, UserSession, VerificationCode

# MongoDB 模型（临时注释，待实现）
# from app.models.backtest import BacktestResultModel
# from app.models.watchlist import WatchlistModel, PositionModel
# from app.models.notification import NotificationModel
# from app.models.notification_rule import NotificationRuleModel
# from app.models.screen_rule import ScreenRuleModel

__all__ = [
    # PostgreSQL 模型
    "User",
    "UserSession",
    "VerificationCode",
    # MongoDB 模型
    # "BacktestResultModel",
    # "WatchlistModel",
    # "PositionModel",
    # "NotificationModel",
    # "NotificationRuleModel",
    # "ScreenRuleModel",
]
