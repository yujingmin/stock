"""
推送规则配置 MongoDB 模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class NotificationRuleModel(BaseModel):
    """推送规则配置 MongoDB 文档"""
    rule_id: str = Field(..., description="规则ID")
    user_id: Optional[str] = Field(None, description="用户ID（预留字段）")

    # 规则基本信息
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    enabled: bool = Field(default=True, description="是否启用")

    # 通知类型过滤
    notification_types: List[str] = Field(
        default_factory=list,
        description="启用的通知类型列表（空表示全部）"
    )

    # 优先级过滤
    min_priority: str = Field(
        default="minor",
        description="最低优先级（urgent/normal/minor）"
    )

    # 时间控制
    quiet_hours_enabled: bool = Field(default=False, description="是否启用免打扰时段")
    quiet_hours_start: Optional[str] = Field(None, description="免打扰开始时间（HH:MM）")
    quiet_hours_end: Optional[str] = Field(None, description="免打扰结束时间（HH:MM）")

    # 频率控制
    frequency_limit_enabled: bool = Field(default=True, description="是否启用频率限制")
    frequency_threshold_minutes: int = Field(
        default=30,
        description="同类型通知最小间隔（分钟）"
    )
    daily_limit: Optional[int] = Field(None, description="每日最大通知数量")

    # 持仓关联
    position_only: bool = Field(
        default=False,
        description="是否仅推送持仓/自选股票相关通知"
    )

    # 自定义过滤条件
    custom_filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="自定义过滤条件（JSON格式）"
    )

    # 推送渠道
    push_channels: List[str] = Field(
        default_factory=lambda: ["in_app"],
        description="推送渠道列表（in_app/wechat/email/sms）"
    )

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
