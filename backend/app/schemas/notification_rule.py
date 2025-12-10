"""
推送规则配置相关 Pydantic schemas
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class NotificationRuleCreate(BaseModel):
    """创建推送规则请求"""
    name: str = Field(..., description="规则名称", max_length=100)
    description: Optional[str] = Field(None, description="规则描述")
    enabled: bool = Field(default=True, description="是否启用")
    notification_types: List[str] = Field(default_factory=list, description="启用的通知类型")
    min_priority: str = Field(default="minor", description="最低优先级")
    quiet_hours_enabled: bool = Field(default=False, description="是否启用免打扰")
    quiet_hours_start: Optional[str] = Field(None, description="免打扰开始时间")
    quiet_hours_end: Optional[str] = Field(None, description="免打扰结束时间")
    frequency_limit_enabled: bool = Field(default=True, description="是否启用频率限制")
    frequency_threshold_minutes: int = Field(default=30, description="频率阈值（分钟）")
    daily_limit: Optional[int] = Field(None, description="每日最大通知数")
    position_only: bool = Field(default=False, description="仅推送持仓相关")
    custom_filters: Dict[str, Any] = Field(default_factory=dict, description="自定义过滤条件")
    push_channels: List[str] = Field(default_factory=lambda: ["in_app"], description="推送渠道")


class NotificationRuleUpdate(BaseModel):
    """更新推送规则请求"""
    name: Optional[str] = Field(None, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    enabled: Optional[bool] = Field(None, description="是否启用")
    notification_types: Optional[List[str]] = Field(None, description="启用的通知类型")
    min_priority: Optional[str] = Field(None, description="最低优先级")
    quiet_hours_enabled: Optional[bool] = Field(None, description="是否启用免打扰")
    quiet_hours_start: Optional[str] = Field(None, description="免打扰开始时间")
    quiet_hours_end: Optional[str] = Field(None, description="免打扰结束时间")
    frequency_limit_enabled: Optional[bool] = Field(None, description="是否启用频率限制")
    frequency_threshold_minutes: Optional[int] = Field(None, description="频率阈值")
    daily_limit: Optional[int] = Field(None, description="每日最大通知数")
    position_only: Optional[bool] = Field(None, description="仅推送持仓相关")
    custom_filters: Optional[Dict[str, Any]] = Field(None, description="自定义过滤条件")
    push_channels: Optional[List[str]] = Field(None, description="推送渠道")


class NotificationRuleResponse(BaseModel):
    """推送规则响应"""
    rule_id: str
    user_id: Optional[str]
    name: str
    description: Optional[str]
    enabled: bool
    notification_types: List[str]
    min_priority: str
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    frequency_limit_enabled: bool
    frequency_threshold_minutes: int
    daily_limit: Optional[int]
    position_only: bool
    custom_filters: Dict[str, Any]
    push_channels: List[str]
    created_at: datetime
    updated_at: datetime
