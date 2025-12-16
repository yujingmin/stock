"""
策略开发 MongoDB 模型
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    """对话状态"""
    ACTIVE = "active"  # 进行中
    COMPLETED = "completed"  # 已完成
    ARCHIVED = "archived"  # 已归档


class StrategyStatus(str, Enum):
    """策略状态"""
    DRAFT = "draft"  # 草稿
    TESTING = "testing"  # 测试中
    ACTIVE = "active"  # 激活
    ARCHIVED = "archived"  # 归档


class ConversationMessageModel(BaseModel):
    """对话消息MongoDB文档"""
    conversation_id: str = Field(..., description="对话ID")
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")

    # 如果消息包含生成的代码
    generated_code: Optional[str] = Field(None, description="生成的策略代码")
    code_language: Optional[str] = Field("python", description="代码语言")

    # 关联的策略版本（如果此消息创建了新版本）
    strategy_version_id: Optional[str] = Field(None, description="关联的策略版本ID")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="消息元数据")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StrategyConversationModel(BaseModel):
    """策略对话MongoDB文档"""
    user_id: str = Field(..., description="用户ID")
    title: str = Field(..., description="对话标题")
    description: Optional[str] = Field(None, description="对话描述")

    # 对话状态
    status: ConversationStatus = Field(default=ConversationStatus.ACTIVE, description="对话状态")

    # 关联的策略（最新版本）
    current_strategy_id: Optional[str] = Field(None, description="当前策略ID")

    # 对话标签
    tags: List[str] = Field(default_factory=list, description="对话标签")

    # 统计信息
    message_count: int = Field(default=0, description="消息数量")
    version_count: int = Field(default=0, description="策略版本数量")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    last_message_at: Optional[datetime] = Field(None, description="最后消息时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StrategyVersionModel(BaseModel):
    """策略版本MongoDB文档"""
    strategy_name: str = Field(..., description="策略名称")
    user_id: str = Field(..., description="用户ID")

    # 关联对话
    conversation_id: Optional[str] = Field(None, description="关联的对话ID")
    message_id: Optional[str] = Field(None, description="生成此版本的消息ID")

    # 策略代码（加密存储）
    code: str = Field(..., description="策略代码")
    code_encrypted: bool = Field(default=False, description="代码是否加密")

    # 版本信息
    version: int = Field(default=1, description="版本号")
    version_description: Optional[str] = Field(None, description="版本说明")

    # 策略元数据
    strategy_type: Optional[str] = Field(None, description="策略类型（多头、CTA、网格等）")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")

    # 回测信息（如果已回测）
    backtest_result_id: Optional[str] = Field(None, description="关联的回测结果ID")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="绩效指标快照")

    # 状态
    status: StrategyStatus = Field(default=StrategyStatus.DRAFT, description="策略状态")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StrategyTemplateModel(BaseModel):
    """策略模板MongoDB文档"""
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")

    # 模板代码
    code: str = Field(..., description="模板代码")

    # 模板元数据
    strategy_type: str = Field(..., description="策略类型")
    difficulty: str = Field(default="intermediate", description="难度级别: beginner/intermediate/advanced")
    risk_level: str = Field(default="medium", description="风险等级: low/medium/high")

    # 适用场景
    suitable_markets: List[str] = Field(default_factory=list, description="适用市场")
    tags: List[str] = Field(default_factory=list, description="标签")

    # 参数说明
    parameters: Dict[str, Any] = Field(default_factory=dict, description="参数说明")

    # 使用统计
    usage_count: int = Field(default=0, description="使用次数")

    # 创建者
    created_by: str = Field(default="system", description="创建者（system或用户ID）")
    is_public: bool = Field(default=True, description="是否公开")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
