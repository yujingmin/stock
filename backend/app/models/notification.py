"""
通知记录 MongoDB 模型
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class NotificationPriority(str, Enum):
    """通知优先级"""
    URGENT = "urgent"  # 紧急：风控触发、异常预警
    NORMAL = "normal"  # 普通：策略信号、持仓提醒
    MINOR = "minor"    # 次要：日常统计、系统消息


class NotificationType(str, Enum):
    """通知类型"""
    RISK_ALERT = "risk_alert"              # 风控预警
    STRATEGY_SIGNAL = "strategy_signal"    # 策略信号
    POSITION_REMINDER = "position_reminder"  # 持仓提醒
    SYSTEM_NOTICE = "system_notice"        # 系统通知
    DATA_ANOMALY = "data_anomaly"          # 数据异常
    BACKTEST_COMPLETE = "backtest_complete"  # 回测完成


class NotificationModel(BaseModel):
    """通知记录 MongoDB 文档"""
    notification_id: str = Field(..., description="通知ID")
    user_id: Optional[str] = Field(None, description="用户ID（预留字段）")

    # 通知基本信息
    type: NotificationType = Field(..., description="通知类型")
    priority: NotificationPriority = Field(..., description="优先级")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")

    # 关联信息
    target_symbol: Optional[str] = Field(None, description="关联股票代码")
    strategy_id: Optional[str] = Field(None, description="关联策略ID")
    task_id: Optional[str] = Field(None, description="关联任务ID")

    # 触发条件
    trigger_condition: Optional[str] = Field(None, description="触发条件描述")
    trigger_value: Optional[float] = Field(None, description="触发值")

    # 扩展数据
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="扩展数据")

    # 状态管理
    read_status: bool = Field(default=False, description="已读状态")
    pushed: bool = Field(default=False, description="是否已推送")
    push_channel: Optional[str] = Field(None, description="推送渠道（wechat/email/sms）")

    # 跟进提醒
    follow_up: bool = Field(default=False, description="是否需要跟进")
    follow_up_time: Optional[datetime] = Field(None, description="跟进提醒时间")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    read_at: Optional[datetime] = Field(None, description="读取时间")
    pushed_at: Optional[datetime] = Field(None, description="推送时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NotificationStatModel(BaseModel):
    """通知统计 MongoDB 文档"""
    stat_id: str = Field(..., description="统计ID")
    period: str = Field(..., description="统计周期（daily/weekly/monthly）")
    start_date: datetime = Field(..., description="统计开始日期")
    end_date: datetime = Field(..., description="统计结束日期")

    # 统计数据
    total_notifications: int = Field(default=0, description="总通知数")
    urgent_count: int = Field(default=0, description="紧急通知数")
    normal_count: int = Field(default=0, description="普通通知数")
    minor_count: int = Field(default=0, description="次要通知数")

    # 按类型统计
    type_distribution: Dict[str, int] = Field(default_factory=dict, description="类型分布")

    # 推送统计
    pushed_count: int = Field(default=0, description="已推送数量")
    read_count: int = Field(default=0, description="已读数量")
    avg_read_time: Optional[float] = Field(None, description="平均阅读时间（秒）")

    # 触发统计
    most_triggered_symbol: Optional[str] = Field(None, description="触发最多的股票")
    most_triggered_strategy: Optional[str] = Field(None, description="触发最多的策略")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
