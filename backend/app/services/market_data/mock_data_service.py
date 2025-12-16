"""
模拟数据服务 - 用于开发和测试
当 akshare 不可用时提供模拟数据
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import random


class MockDataService:
    """模拟数据服务"""

    @staticmethod
    def get_stock_realtime_quote(symbol: str) -> Dict[str, Any]:
        """获取模拟实时行情"""
        base_price = 10.0 + (int(symbol) % 100)  # 根据股票代码生成基础价格

        price = base_price + random.uniform(-2, 2)
        prev_close = price - random.uniform(-1, 1)
        change = price - prev_close
        change_percent = (change / prev_close) * 100

        return {
            "symbol": symbol,
            "name": f"股票{symbol}",
            "price": round(price, 2),
            "change_percent": round(change_percent, 2),
            "change_amount": round(change, 2),
            "volume": random.randint(1000000, 10000000),
            "amount": random.randint(10000000, 100000000),
            "high": round(price + random.uniform(0, 1), 2),
            "low": round(price - random.uniform(0, 1), 2),
            "open": round(prev_close + random.uniform(-0.5, 0.5), 2),
            "close_yesterday": round(prev_close, 2),
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def get_stock_hist_kline(
        symbol: str,
        period: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
    ) -> pd.DataFrame:
        """获取模拟历史K线"""
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

        start = datetime.strptime(start_date, "%Y%m%d")
        end = datetime.strptime(end_date, "%Y%m%d")

        dates = pd.date_range(start=start, end=end, freq='D')

        # 生成随机价格走势
        base_price = 10.0 + (int(symbol) % 100)
        prices = [base_price]

        for _ in range(len(dates) - 1):
            # 随机游走
            change = random.uniform(-0.5, 0.5)
            new_price = max(prices[-1] + change, base_price * 0.5)  # 确保价格不会太低
            prices.append(new_price)

        data = []
        for i, date in enumerate(dates):
            open_price = prices[i] + random.uniform(-0.2, 0.2)
            close_price = prices[i]
            high_price = max(open_price, close_price) + random.uniform(0, 0.5)
            low_price = min(open_price, close_price) - random.uniform(0, 0.5)

            data.append({
                "date": date,
                "open": round(open_price, 2),
                "close": round(close_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "volume": random.randint(1000000, 10000000),
                "amount": random.randint(10000000, 100000000),
                "amplitude": round(random.uniform(1, 5), 2),
                "change_percent": round(random.uniform(-3, 3), 2),
                "change_amount": round(random.uniform(-1, 1), 2),
                "turnover": round(random.uniform(0.5, 5), 2),
            })

        df = pd.DataFrame(data)
        return df

    @staticmethod
    def get_stock_indicators(symbol: str) -> Dict[str, Any]:
        """获取模拟股票指标"""
        return {
            "symbol": symbol,
            "pe_ratio": round(random.uniform(10, 50), 2),
            "pb_ratio": round(random.uniform(1, 10), 2),
            "dividend_yield": round(random.uniform(0.5, 5), 2),
            "roe": round(random.uniform(5, 25), 2),
            "total_market_cap": random.randint(1000000000, 100000000000),
            "circulating_market_cap": random.randint(500000000, 50000000000),
        }

    @staticmethod
    def get_stock_financial_report(symbol: str, report_type: str = "balance_sheet") -> pd.DataFrame:
        """获取模拟财务报表"""
        dates = [datetime.now() - timedelta(days=i*90) for i in range(4)]

        data = []
        for date in dates:
            data.append({
                "报告期": date.strftime("%Y-%m-%d"),
                "总资产": random.randint(1000000000, 10000000000),
                "总负债": random.randint(500000000, 5000000000),
                "净资产": random.randint(500000000, 5000000000),
                "营业收入": random.randint(100000000, 1000000000),
                "净利润": random.randint(10000000, 100000000),
            })

        return pd.DataFrame(data)

    @staticmethod
    def get_stock_list() -> List[Dict[str, str]]:
        """获取模拟股票列表"""
        stocks = []
        for i in range(1, 101):  # 生成100只股票
            code = f"{i:06d}"
            stocks.append({
                "symbol": code,
                "name": f"股票{code}",
                "market": "A股",
            })
        return stocks


# 全局实例
mock_data_service = MockDataService()
