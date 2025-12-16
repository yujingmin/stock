"""
akshare 数据接入客户端
实现 A 股实时行情、财务报表、宏观经济数据获取
"""
import akshare as ak
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
from functools import wraps, lru_cache
import logging
import time

logger = logging.getLogger(__name__)

# 简单的内存缓存
_cache = {}
_cache_ttl = {}  # 缓存过期时间


def get_from_cache(key: str) -> Optional[Any]:
    """从缓存获取数据"""
    if key in _cache:
        # 检查是否过期
        if time.time() < _cache_ttl.get(key, 0):
            logger.debug(f"缓存命中: {key}")
            return _cache[key]
        else:
            # 过期，删除缓存
            del _cache[key]
            del _cache_ttl[key]
    return None


def set_to_cache(key: str, value: Any, ttl: int = 60):
    """设置缓存数据

    Args:
        key: 缓存键
        value: 缓存值
        ttl: 过期时间(秒)，默认60秒
    """
    _cache[key] = value
    _cache_ttl[key] = time.time() + ttl
    logger.debug(f"缓存已设置: {key}, TTL={ttl}秒")


def clean_numeric_value(value: Any, default: float = 0.0) -> float:
    """
    清理数值,将NaN、Infinity等不合法值转换为默认值

    Args:
        value: 原始值
        default: 默认值

    Returns:
        清理后的浮点数
    """
    try:
        num = float(value)
        # 检查是否为NaN或Infinity
        if pd.isna(num) or np.isinf(num):
            return default
        return num
    except (ValueError, TypeError):
        return default


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    清理DataFrame中的NaN和Infinity值

    Args:
        df: 原始DataFrame

    Returns:
        清理后的DataFrame
    """
    # 替换NaN和Infinity为None（JSON中会变成null）
    df = df.replace([np.inf, -np.inf], np.nan)
    # 将数值列的NaN替换为0
    numeric_columns = df.select_dtypes(include=[np.number]).columns
    df[numeric_columns] = df[numeric_columns].fillna(0)
    # 将字符串列的NaN替换为空字符串
    string_columns = df.select_dtypes(include=['object']).columns
    df[string_columns] = df[string_columns].fillna('')
    return df


def retry_on_failure(max_retries: int = 5, delay: float = 2.0, use_cache: bool = False, cache_ttl: int = 60):
    """装饰器：异常重试机制

    Args:
        max_retries: 最大重试次数，增加到5次
        delay: 基础延迟时间(秒)，增加到2秒
        use_cache: 是否使用缓存
        cache_ttl: 缓存过期时间(秒)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 如果启用缓存，先尝试从缓存获取
            if use_cache:
                # 构建缓存键
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                cached_result = get_from_cache(cache_key)
                if cached_result is not None:
                    return cached_result

            last_exception = None
            for attempt in range(max_retries):
                try:
                    result = await func(*args, **kwargs)

                    # 成功后保存到缓存
                    if use_cache:
                        cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                        set_to_cache(cache_key, result, cache_ttl)

                    return result

                except Exception as e:
                    last_exception = e
                    error_msg = str(e)

                    # 判断错误类型
                    is_connection_error = any(keyword in error_msg.lower() for keyword in [
                        'connection', 'timeout', 'network', 'remote', 'aborted'
                    ])

                    logger.warning(
                        f"尝试 {attempt + 1}/{max_retries} 失败: {func.__name__}. "
                        f"错误类型: {'网络连接错误' if is_connection_error else '其他错误'}. "
                        f"错误详情: {error_msg[:100]}"
                    )

                    if attempt < max_retries - 1:
                        # 对于网络错误，使用指数退避策略
                        if is_connection_error:
                            wait_time = delay * (2 ** attempt)  # 指数退避: 2, 4, 8, 16秒
                        else:
                            wait_time = delay * (attempt + 1)  # 线性增长: 2, 4, 6, 8秒

                        logger.info(f"等待 {wait_time} 秒后重试...")
                        await asyncio.sleep(wait_time)
                    else:
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

    @retry_on_failure(max_retries=5, delay=2.0, use_cache=True, cache_ttl=30)
    async def get_stock_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票实时行情（使用历史数据的最新一条）

        Args:
            symbol: 股票代码，如 "000001"（不带市场前缀）

        Returns:
            实时行情数据字典
        """
        try:
            # 获取最近3天的历史数据（确保能获取到最新交易日）
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")

            # 使用stock_zh_a_hist获取历史数据
            df = await self._run_in_executor(
                ak.stock_zh_a_hist,
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=""
            )

            if df.empty:
                raise ValueError(f"未找到股票代码: {symbol}")

            # 获取最新一条数据
            latest = df.iloc[-1]

            # 计算涨跌幅和涨跌额
            if len(df) >= 2:
                prev_close = clean_numeric_value(df.iloc[-2]['收盘'])
            else:
                prev_close = clean_numeric_value(latest['收盘'])

            current_price = clean_numeric_value(latest['收盘'])
            change_amount = current_price - prev_close
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0.0

            return {
                "symbol": symbol,
                "name": f"股票{symbol}",  # akshare的hist接口不返回名称
                "price": current_price,
                "change_percent": change_percent,
                "change_amount": change_amount,
                "volume": clean_numeric_value(latest['成交量']),
                "amount": clean_numeric_value(latest['成交额']),
                "high": clean_numeric_value(latest['最高']),
                "low": clean_numeric_value(latest['最低']),
                "open": clean_numeric_value(latest['开盘']),
                "close_yesterday": prev_close,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"获取股票 {symbol} 实时行情失败: {str(e)}")
            raise

    @retry_on_failure(max_retries=5, delay=2.0, use_cache=True, cache_ttl=300)
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

            # 清理数据
            return clean_dataframe(df)

        except Exception as e:
            logger.error(f"获取股票 {symbol} 历史K线失败: {str(e)}")
            raise

    @retry_on_failure(max_retries=5, delay=2.0, use_cache=True, cache_ttl=600)
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

            return clean_dataframe(df)

        except Exception as e:
            logger.error(f"获取股票 {symbol} 财务报表失败: {str(e)}")
            raise

    @retry_on_failure(max_retries=5, delay=2.0, use_cache=True, cache_ttl=300)
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

    @retry_on_failure(max_retries=5, delay=2.0, use_cache=True, cache_ttl=3600)
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

            return clean_dataframe(df)

        except Exception as e:
            logger.error(f"获取宏观指标 {indicator_type} 失败: {str(e)}")
            raise

    @retry_on_failure(max_retries=5, delay=2.0, use_cache=True, cache_ttl=3600)
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
# trigger reload 2025年12月11日 22:33:08
