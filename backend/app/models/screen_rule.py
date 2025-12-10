"""
筛选规则数据模型（存储在 MongoDB）
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ScreenRule(BaseModel):
    """筛选规则模型"""
    id: Optional[str] = Field(None, alias="_id", description="规则ID")
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    conditions: Dict[str, Any] = Field(..., description="筛选条件")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
