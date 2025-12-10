"""
自选股和持仓相关 Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class WatchlistCreate(BaseModel):
    """创建自选股请求"""
    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    enable_notification: bool = Field(default=True, description="是否开启通知")
    notify_types: List[str] = Field(default_factory=lambda: ["strategy_signal", "risk_alert"], description="通知类型")
    price_alert_upper: Optional[float] = Field(None, description="价格上限提醒")
    price_alert_lower: Optional[float] = Field(None, description="价格下限提醒")


class WatchlistUpdate(BaseModel):
    """更新自选股请求"""
    name: Optional[str] = Field(None, description="股票名称")
    enable_notification: Optional[bool] = Field(None, description="是否开启通知")
    notify_types: Optional[List[str]] = Field(None, description="通知类型")
    price_alert_upper: Optional[float] = Field(None, description="价格上限提醒")
    price_alert_lower: Optional[float] = Field(None, description="价格下限提醒")


class WatchlistResponse(BaseModel):
    """自选股响应"""
    watchlist_id: str
    user_id: Optional[str]
    symbol: str
    name: Optional[str]
    enable_notification: bool
    notify_types: List[str]
    price_alert_upper: Optional[float]
    price_alert_lower: Optional[float]
    added_at: datetime
    updated_at: datetime


class PositionCreate(BaseModel):
    """创建持仓请求"""
    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    quantity: int = Field(..., description="持仓数量", gt=0)
    avg_cost: float = Field(..., description="持仓成本", gt=0)
    enable_notification: bool = Field(default=True, description="是否开启通知")
    stop_loss_price: Optional[float] = Field(None, description="止损价格")
    take_profit_price: Optional[float] = Field(None, description="止盈价格")


class PositionUpdate(BaseModel):
    """更新持仓请求"""
    name: Optional[str] = Field(None, description="股票名称")
    quantity: Optional[int] = Field(None, description="持仓数量", gt=0)
    avg_cost: Optional[float] = Field(None, description="持仓成本", gt=0)
    current_price: Optional[float] = Field(None, description="当前价格")
    enable_notification: Optional[bool] = Field(None, description="是否开启通知")
    stop_loss_price: Optional[float] = Field(None, description="止损价格")
    take_profit_price: Optional[float] = Field(None, description="止盈价格")


class PositionResponse(BaseModel):
    """持仓响应"""
    position_id: str
    user_id: Optional[str]
    symbol: str
    name: Optional[str]
    quantity: int
    avg_cost: float
    current_price: Optional[float]
    profit_loss: Optional[float]
    profit_loss_ratio: Optional[float]
    enable_notification: bool
    stop_loss_price: Optional[float]
    take_profit_price: Optional[float]
    opened_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
