"""
回测结果 MongoDB 模型
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class BacktestResultModel(BaseModel):
    """回测结果MongoDB文档"""
    task_id: str = Field(..., description="任务ID")
    symbol: str = Field(..., description="股票代码")
    strategy_type: str = Field(..., description="策略类型")

    # 配置信息
    config: Dict[str, Any] = Field(..., description="回测配置")

    # 绩效指标
    metrics: Dict[str, Any] = Field(..., description="绩效指标")

    # 交易记录
    trading_records: List[Dict[str, Any]] = Field(default_factory=list, description="交易记录")

    # 权益曲线
    equity_curve: List[Dict[str, Any]] = Field(default_factory=list, description="权益曲线")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
