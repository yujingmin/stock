"""
通知相关 Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from ...models.notification import NotificationPriority, NotificationType


class NotificationCreate(BaseModel):
    """创建通知请求"""
    type: NotificationType = Field(..., description="通知类型")
    priority: NotificationPriority = Field(..., description="优先级")
    title: str = Field(..., description="通知标题", max_length=200)
    content: str = Field(..., description="通知内容")
    target_symbol: Optional[str] = Field(None, description="关联股票代码")
    strategy_id: Optional[str] = Field(None, description="关联策略ID")
    task_id: Optional[str] = Field(None, description="关联任务ID")
    trigger_condition: Optional[str] = Field(None, description="触发条件描述")
    trigger_value: Optional[float] = Field(None, description="触发值")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="扩展数据")
    follow_up: bool = Field(default=False, description="是否需要跟进")
    follow_up_time: Optional[datetime] = Field(None, description="跟进提醒时间")


class NotificationUpdate(BaseModel):
    """更新通知请求"""
    read_status: Optional[bool] = Field(None, description="已读状态")
    follow_up: Optional[bool] = Field(None, description="是否需要跟进")
    follow_up_time: Optional[datetime] = Field(None, description="跟进提醒时间")


class NotificationResponse(BaseModel):
    """通知响应"""
    notification_id: str
    user_id: Optional[str]
    type: NotificationType
    priority: NotificationPriority
    title: str
    content: str
    target_symbol: Optional[str]
    strategy_id: Optional[str]
    task_id: Optional[str]
    trigger_condition: Optional[str]
    trigger_value: Optional[float]
    extra_data: Dict[str, Any]
    read_status: bool
    pushed: bool
    push_channel: Optional[str]
    follow_up: bool
    follow_up_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    read_at: Optional[datetime]
    pushed_at: Optional[datetime]


class NotificationListResponse(BaseModel):
    """通知列表响应"""
    total: int = Field(..., description="总数")
    unread_count: int = Field(..., description="未读数量")
    notifications: List[NotificationResponse] = Field(..., description="通知列表")


class NotificationQuery(BaseModel):
    """通知查询条件"""
    type: Optional[NotificationType] = Field(None, description="通知类型")
    priority: Optional[NotificationPriority] = Field(None, description="优先级")
    read_status: Optional[bool] = Field(None, description="已读状态")
    target_symbol: Optional[str] = Field(None, description="股票代码")
    strategy_id: Optional[str] = Field(None, description="策略ID")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    follow_up: Optional[bool] = Field(None, description="仅显示需要跟进的")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量")
    offset: int = Field(default=0, ge=0, description="偏移量")


class NotificationStatResponse(BaseModel):
    """通知统计响应"""
    period: str
    start_date: datetime
    end_date: datetime
    total_notifications: int
    urgent_count: int
    normal_count: int
    minor_count: int
    type_distribution: Dict[str, int]
    pushed_count: int
    read_count: int
    avg_read_time: Optional[float]
    most_triggered_symbol: Optional[str]
    most_triggered_strategy: Optional[str]
