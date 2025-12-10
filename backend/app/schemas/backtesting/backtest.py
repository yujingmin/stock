"""
回测相关数据模型
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class StrategyType(str, Enum):
    """策略类型"""
    SIMPLE_MA = "simple_ma"  # 简单移动平均线
    CUSTOM = "custom"  # 自定义策略


class BacktestStatus(str, Enum):
    """回测任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StrategyConfig(BaseModel):
    """策略配置"""
    strategy_type: StrategyType = Field(..., description="策略类型")
    strategy_params: Dict[str, Any] = Field(default_factory=dict, description="策略参数")

    class Config:
        schema_extra = {
            "example": {
                "strategy_type": "simple_ma",
                "strategy_params": {
                    "fast_period": 5,
                    "slow_period": 20,
                    "printlog": False
                }
            }
        }


class BacktestConfig(BaseModel):
    """回测配置"""
    # 股票信息
    symbol: str = Field(..., description="股票代码")
    start_date: Optional[str] = Field(None, description="回测开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="回测结束日期 (YYYY-MM-DD)")
    period: str = Field("daily", description="K线周期 (daily/weekly/monthly)")

    # 初始资金
    initial_cash: float = Field(100000.0, ge=1000.0, description="初始资金")

    # 交易成本
    commission: float = Field(0.0003, ge=0.0, le=0.01, description="佣金费率")
    stamp_duty: float = Field(0.001, ge=0.0, le=0.01, description="印花税")
    min_commission: float = Field(5.0, ge=0.0, description="最低佣金")
    slippage: float = Field(0.001, ge=0.0, le=0.1, description="滑点")

    # 策略配置
    strategy: StrategyConfig = Field(..., description="策略配置")

    class Config:
        schema_extra = {
            "example": {
                "symbol": "000001",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "period": "daily",
                "initial_cash": 100000.0,
                "commission": 0.0003,
                "stamp_duty": 0.001,
                "min_commission": 5.0,
                "slippage": 0.001,
                "strategy": {
                    "strategy_type": "simple_ma",
                    "strategy_params": {
                        "fast_period": 5,
                        "slow_period": 20
                    }
                }
            }
        }


class TradingRecord(BaseModel):
    """交易记录"""
    date: str = Field(..., description="交易日期")
    action: str = Field(..., description="交易动作 (buy/sell)")
    price: float = Field(..., description="交易价格")
    size: int = Field(..., description="交易数量")
    commission: float = Field(..., description="交易佣金")
    value: float = Field(..., description="交易金额")


class PerformanceMetrics(BaseModel):
    """绩效指标"""
    # 收益指标
    initial_value: float = Field(..., description="初始资金")
    final_value: float = Field(..., description="最终资金")
    total_return: float = Field(..., description="总收益率")
    annual_return: float = Field(..., description="年化收益率")

    # 风险指标
    sharpe_ratio: float = Field(..., description="夏普比率")
    max_drawdown: float = Field(..., description="最大回撤")

    # 交易指标
    total_trades: int = Field(..., description="总交易次数")
    won_trades: int = Field(..., description="盈利交易次数")
    lost_trades: int = Field(..., description="亏损交易次数")
    win_rate: float = Field(..., description="胜率")

    class Config:
        schema_extra = {
            "example": {
                "initial_value": 100000.0,
                "final_value": 115000.0,
                "total_return": 0.15,
                "annual_return": 0.15,
                "sharpe_ratio": 1.5,
                "max_drawdown": 0.08,
                "total_trades": 20,
                "won_trades": 12,
                "lost_trades": 8,
                "win_rate": 0.6
            }
        }


class BacktestResult(BaseModel):
    """回测结果"""
    task_id: str = Field(..., description="任务ID")
    config: BacktestConfig = Field(..., description="回测配置")
    metrics: PerformanceMetrics = Field(..., description="绩效指标")
    trading_records: List[TradingRecord] = Field(default_factory=list, description="交易记录")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class BacktestTask(BaseModel):
    """回测任务"""
    task_id: str = Field(..., description="任务ID")
    status: BacktestStatus = Field(..., description="任务状态")
    config: BacktestConfig = Field(..., description="回测配置")
    result: Optional[BacktestResult] = Field(None, description="回测结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
