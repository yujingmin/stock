"""
用户自选股和持仓 MongoDB 模型
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class WatchlistModel(BaseModel):
    """用户自选股 MongoDB 文档"""
    watchlist_id: str = Field(..., description="自选股ID")
    user_id: Optional[str] = Field(None, description="用户ID（预留字段）")
    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")

    # 监控设置
    enable_notification: bool = Field(default=True, description="是否开启通知")
    notify_types: List[str] = Field(default_factory=list, description="通知类型列表")

    # 价格提醒
    price_alert_upper: Optional[float] = Field(None, description="价格上限提醒")
    price_alert_lower: Optional[float] = Field(None, description="价格下限提醒")

    # 时间戳
    added_at: datetime = Field(default_factory=datetime.now, description="添加时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PositionModel(BaseModel):
    """用户持仓 MongoDB 文档"""
    position_id: str = Field(..., description="持仓ID")
    user_id: Optional[str] = Field(None, description="用户ID（预留字段）")
    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")

    # 持仓信息
    quantity: int = Field(..., description="持仓数量")
    avg_cost: float = Field(..., description="持仓成本")
    current_price: Optional[float] = Field(None, description="当前价格")

    # 盈亏信息
    profit_loss: Optional[float] = Field(None, description="盈亏金额")
    profit_loss_ratio: Optional[float] = Field(None, description="盈亏比例")

    # 监控设置
    enable_notification: bool = Field(default=True, description="是否开启通知")
    stop_loss_price: Optional[float] = Field(None, description="止损价格")
    take_profit_price: Optional[float] = Field(None, description="止盈价格")

    # 时间戳
    opened_at: datetime = Field(default_factory=datetime.now, description="建仓时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    closed_at: Optional[datetime] = Field(None, description="平仓时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
