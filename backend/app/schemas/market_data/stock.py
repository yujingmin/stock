"""
股票数据相关的 Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class StockRealtimeQuote(BaseModel):
    """股票实时行情"""
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    price: float = Field(..., description="最新价")
    change_percent: float = Field(..., description="涨跌幅(%)")
    change_amount: float = Field(..., description="涨跌额")
    volume: float = Field(..., description="成交量")
    amount: float = Field(..., description="成交额")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    open: float = Field(..., description="今开")
    close_yesterday: float = Field(..., description="昨收")
    timestamp: str = Field(..., description="数据时间戳")


class StockKLineData(BaseModel):
    """K线数据单条记录"""
    date: str = Field(..., description="日期")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    amount: Optional[float] = Field(None, description="成交额")
    change_percent: Optional[float] = Field(None, description="涨跌幅")


class StockKLineResponse(BaseModel):
    """K线数据响应"""
    symbol: str = Field(..., description="股票代码")
    period: str = Field(..., description="周期")
    data: List[StockKLineData] = Field(..., description="K线数据列表")
    count: int = Field(..., description="数据条数")


class StockIndicators(BaseModel):
    """股票主要指标"""
    symbol: str = Field(..., description="股票代码")
    pe_ratio: Optional[float] = Field(None, description="市盈率")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    dividend_yield: Optional[float] = Field(None, description="股息率(%)")
    roe: Optional[float] = Field(None, description="净资产收益率(%)")
    total_market_cap: Optional[float] = Field(None, description="总市值")
    circulating_market_cap: Optional[float] = Field(None, description="流通市值")


class StockListItem(BaseModel):
    """股票列表项"""
    symbol: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场")


class StockScreenFilter(BaseModel):
    """股票筛选条件"""
    min_pe: Optional[float] = Field(None, description="最小市盈率")
    max_pe: Optional[float] = Field(None, description="最大市盈率")
    min_pb: Optional[float] = Field(None, description="最小市净率")
    max_pb: Optional[float] = Field(None, description="最大市净率")
    min_dividend_yield: Optional[float] = Field(None, description="最小股息率")
    min_market_cap: Optional[float] = Field(None, description="最小市值（亿元）")


class TechnicalIndicators(BaseModel):
    """技术指标数据"""
    ma5: Optional[float] = Field(None, description="5日均线")
    ma10: Optional[float] = Field(None, description="10日均线")
    ma20: Optional[float] = Field(None, description="20日均线")
    ma60: Optional[float] = Field(None, description="60日均线")
    macd: Optional[float] = Field(None, description="MACD")
    macd_signal: Optional[float] = Field(None, description="MACD信号线")
    macd_hist: Optional[float] = Field(None, description="MACD柱状图")
    k: Optional[float] = Field(None, description="KDJ K值")
    d: Optional[float] = Field(None, description="KDJ D值")
    j: Optional[float] = Field(None, description="KDJ J值")
    rsi14: Optional[float] = Field(None, description="RSI(14)")
    boll_upper: Optional[float] = Field(None, description="布林带上轨")
    boll_middle: Optional[float] = Field(None, description="布林带中轨")
    boll_lower: Optional[float] = Field(None, description="布林带下轨")
