"""
akshare 数据接入客户端
实现 A 股实时行情、财务报表、宏观经济数据获取
"""
import akshare as ak
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """装饰器：异常重试机制"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"尝试 {attempt + 1}/{max_retries} 失败: {func.__name__}. "
                        f"错误: {str(e)}"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))

            logger.error(f"{func.__name__} 在 {max_retries} 次尝试后仍然失败")
            raise last_exception
        return wrapper
    return decorator


class AkShareClient:
    """akshare 数据客户端"""

    @staticmethod
    async def _run_in_executor(func, *args, **kwargs):
        """在线程池中运行同步函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    @retry_on_failure(max_retries=3)
    async def get_stock_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票实时行情

        Args:
            symbol: 股票代码，如 "000001"（不带市场前缀）

        Returns:
            实时行情数据字典
        """
        try:
            # 获取实时行情快照
            df = await self._run_in_executor(ak.stock_zh_a_spot_em)

            # 筛选指定股票
            stock_data = df[df['代码'] == symbol]

            if stock_data.empty:
                raise ValueError(f"未找到股票代码: {symbol}")

            # 转换为字典
            data = stock_data.iloc[0].to_dict()

            return {
                "symbol": symbol,
                "name": data.get("名称", ""),
                "price": float(data.get("最新价", 0)),
                "change_percent": float(data.get("涨跌幅", 0)),
                "change_amount": float(data.get("涨跌额", 0)),
                "volume": float(data.get("成交量", 0)),
                "amount": float(data.get("成交额", 0)),
                "high": float(data.get("最高", 0)),
                "low": float(data.get("最低", 0)),
                "open": float(data.get("今开", 0)),
                "close_yesterday": float(data.get("昨收", 0)),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"获取股票 {symbol} 实时行情失败: {str(e)}")
            raise

    @retry_on_failure(max_retries=3)
    async def get_stock_hist_kline(
        self,
        symbol: str,
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取股票历史 K 线数据

        Args:
            symbol: 股票代码
            period: 周期，daily/weekly/monthly
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            adjust: 复权类型，qfq(前复权)/hfq(后复权)/不复权

        Returns:
            K线数据 DataFrame
        """
        try:
            # 如果没有指定日期，默认获取最近10年
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365*10)).strftime("%Y%m%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")

            df = await self._run_in_executor(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            # 标准化列名
            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "change_percent",
                "涨跌额": "change_amount",
                "换手率": "turnover",
            })

            return df

        except Exception as e:
            logger.error(f"获取股票 {symbol} 历史K线失败: {str(e)}")
            raise

    @retry_on_failure(max_retries=3)
    async def get_stock_financial_report(
        self,
        symbol: str,
        report_type: str = "balance_sheet"
    ) -> pd.DataFrame:
        """
        获取上市公司财务报表

        Args:
            symbol: 股票代码
            report_type: 报表类型
                - balance_sheet: 资产负债表
                - income_statement: 利润表
                - cash_flow: 现金流量表

        Returns:
            财务报表 DataFrame
        """
        try:
            if report_type == "balance_sheet":
                df = await self._run_in_executor(
                    ak.stock_financial_abstract_ths,
                    symbol=symbol,
                    indicator="资产负债表"
                )
            elif report_type == "income_statement":
                df = await self._run_in_executor(
                    ak.stock_financial_abstract_ths,
                    symbol=symbol,
                    indicator="利润表"
                )
            elif report_type == "cash_flow":
                df = await self._run_in_executor(
                    ak.stock_financial_abstract_ths,
                    symbol=symbol,
                    indicator="现金流量表"
                )
            else:
                raise ValueError(f"不支持的报表类型: {report_type}")

            return df

        except Exception as e:
            logger.error(f"获取股票 {symbol} 财务报表失败: {str(e)}")
            raise

    @retry_on_failure(max_retries=3)
    async def get_stock_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票主要指标

        Args:
            symbol: 股票代码

        Returns:
            主要指标字典（市盈率、市净率、股息率等）
        """
        try:
            df = await self._run_in_executor(
                ak.stock_individual_info_em,
                symbol=symbol
            )

            indicators = {}
            for _, row in df.iterrows():
                key = row['item']
                value = row['value']
                indicators[key] = value

            return {
                "symbol": symbol,
                "pe_ratio": indicators.get("市盈率-动态", None),
                "pb_ratio": indicators.get("市净率", None),
                "dividend_yield": indicators.get("股息率", None),
                "roe": indicators.get("净资产收益率", None),
                "total_market_cap": indicators.get("总市值", None),
                "circulating_market_cap": indicators.get("流通市值", None),
            }

        except Exception as e:
            logger.error(f"获取股票 {symbol} 指标失败: {str(e)}")
            raise

    @retry_on_failure(max_retries=3)
    async def get_macro_indicator(
        self,
        indicator_type: str
    ) -> pd.DataFrame:
        """
        获取宏观经济指标

        Args:
            indicator_type: 指标类型
                - gdp: GDP 数据
                - cpi: CPI 数据
                - ppi: PPI 数据
                - pmi: PMI 数据

        Returns:
            宏观指标 DataFrame
        """
        try:
            if indicator_type == "gdp":
                df = await self._run_in_executor(ak.macro_china_gdp)
            elif indicator_type == "cpi":
                df = await self._run_in_executor(ak.macro_china_cpi)
            elif indicator_type == "ppi":
                df = await self._run_in_executor(ak.macro_china_ppi)
            elif indicator_type == "pmi":
                df = await self._run_in_executor(ak.macro_china_pmi)
            else:
                raise ValueError(f"不支持的宏观指标类型: {indicator_type}")

            return df

        except Exception as e:
            logger.error(f"获取宏观指标 {indicator_type} 失败: {str(e)}")
            raise

    @retry_on_failure(max_retries=3)
    async def get_stock_list(self) -> List[Dict[str, str]]:
        """
        获取 A 股股票列表

        Returns:
            股票列表
        """
        try:
            df = await self._run_in_executor(ak.stock_zh_a_spot_em)

            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    "symbol": row["代码"],
                    "name": row["名称"],
                    "market": "A股",
                })

            return stocks

        except Exception as e:
            logger.error(f"获取股票列表失败: {str(e)}")
            raise


# 全局客户端实例
akshare_client = AkShareClient()
