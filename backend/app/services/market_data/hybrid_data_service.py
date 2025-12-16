"""
混合数据服务 - 结合真实 akshare 数据和模拟数据
根据接口稳定性测试结果,自动选择合适的数据源
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime

from .akshare_client import akshare_client
from .mock_data_service import mock_data_service

logger = logging.getLogger(__name__)


class HybridDataService:
    """
    混合数据服务

    根据 akshare 接口稳定性测试结果:
    - 稳定接口(100%成功率): 使用真实 akshare 数据
      * 财务报表
      * 宏观经济数据

    - 不可用接口(0%成功率): 使用模拟数据
      * 股票列表
      * 实时行情
      * 历史K线
      * 股票指标
    """

    def __init__(self, use_mock_for_unstable: bool = True):
        """
        初始化混合数据服务

        Args:
            use_mock_for_unstable: 对不稳定接口是否使用模拟数据,默认 True
        """
        self.use_mock_for_unstable = use_mock_for_unstable
        logger.info(f"混合数据服务已初始化 (不稳定接口使用模拟数据: {use_mock_for_unstable})")

    async def get_stock_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票实时行情

        稳定性: 不可用 (0% 成功率)
        数据源: Mock 数据
        """
        if self.use_mock_for_unstable:
            logger.info(f"使用模拟数据获取股票 {symbol} 实时行情")
            return mock_data_service.get_stock_realtime_quote(symbol)
        else:
            logger.info(f"尝试使用 akshare 获取股票 {symbol} 实时行情 (可能失败)")
            try:
                return await akshare_client.get_stock_realtime_quote(symbol)
            except Exception as e:
                logger.error(f"akshare 获取失败,回退到模拟数据: {str(e)[:100]}")
                return mock_data_service.get_stock_realtime_quote(symbol)

    async def get_stock_hist_kline(
        self,
        symbol: str,
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> pd.DataFrame:
        """
        获取股票历史K线

        稳定性: 不可用 (0% 成功率)
        数据源: Mock 数据
        """
        if self.use_mock_for_unstable:
            logger.info(f"使用模拟数据获取股票 {symbol} 历史K线")
            return mock_data_service.get_stock_hist_kline(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
        else:
            logger.info(f"尝试使用 akshare 获取股票 {symbol} 历史K线 (可能失败)")
            try:
                return await akshare_client.get_stock_hist_kline(
                    symbol=symbol,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust
                )
            except Exception as e:
                logger.error(f"akshare 获取失败,回退到模拟数据: {str(e)[:100]}")
                return mock_data_service.get_stock_hist_kline(
                    symbol=symbol,
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    adjust=adjust
                )

    async def get_stock_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票指标

        稳定性: 不可用 (0% 成功率)
        数据源: Mock 数据
        """
        if self.use_mock_for_unstable:
            logger.info(f"使用模拟数据获取股票 {symbol} 指标")
            return mock_data_service.get_stock_indicators(symbol)
        else:
            logger.info(f"尝试使用 akshare 获取股票 {symbol} 指标 (可能失败)")
            try:
                return await akshare_client.get_stock_indicators(symbol)
            except Exception as e:
                logger.error(f"akshare 获取失败,回退到模拟数据: {str(e)[:100]}")
                return mock_data_service.get_stock_indicators(symbol)

    async def get_stock_financial_report(
        self,
        symbol: str,
        report_type: str = "balance_sheet"
    ) -> pd.DataFrame:
        """
        获取股票财务报表

        稳定性: 稳定 (100% 成功率)
        数据源: akshare 真实数据 (优先) -> Mock 数据 (降级)
        """
        logger.info(f"使用 akshare 获取股票 {symbol} 财务报表 ({report_type})")
        try:
            return await akshare_client.get_stock_financial_report(symbol, report_type)
        except Exception as e:
            logger.error(f"akshare 获取财务报表失败,回退到模拟数据: {str(e)[:100]}")
            return mock_data_service.get_stock_financial_report(symbol, report_type)

    async def get_macro_indicator(self, indicator_type: str) -> pd.DataFrame:
        """
        获取宏观经济指标

        稳定性: 稳定 (100% 成功率)
        数据源: akshare 真实数据 (优先) -> Mock 数据 (降级)
        """
        logger.info(f"使用 akshare 获取宏观指标 ({indicator_type})")
        try:
            return await akshare_client.get_macro_indicator(indicator_type)
        except Exception as e:
            logger.error(f"akshare 获取宏观指标失败,回退到模拟数据: {str(e)[:100]}")
            # Mock 服务暂不支持宏观数据,返回空 DataFrame
            logger.warning(f"模拟数据服务不支持宏观指标,返回空数据")
            return pd.DataFrame()

    async def get_stock_list(self) -> List[Dict[str, str]]:
        """
        获取股票列表

        稳定性: 不可用 (0% 成功率)
        数据源: Mock 数据
        """
        if self.use_mock_for_unstable:
            logger.info("使用模拟数据获取股票列表")
            return mock_data_service.get_stock_list()
        else:
            logger.info("尝试使用 akshare 获取股票列表 (可能失败)")
            try:
                return await akshare_client.get_stock_list()
            except Exception as e:
                logger.error(f"akshare 获取失败,回退到模拟数据: {str(e)[:100]}")
                return mock_data_service.get_stock_list()


# 全局混合数据服务实例
hybrid_data_service = HybridDataService(use_mock_for_unstable=True)
