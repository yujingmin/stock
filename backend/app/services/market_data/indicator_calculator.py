"""
技术指标计算模块
实现常用的量化因子计算（MACD、KDJ、均线等）
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """技术指标计算器"""

    @staticmethod
    def calculate_ma(df: pd.DataFrame, periods: list = [5, 10, 20, 60]) -> pd.DataFrame:
        """
        计算移动平均线（MA）

        Args:
            df: K线数据，必须包含 close 列
            periods: MA 周期列表

        Returns:
            包含 MA 指标的 DataFrame
        """
        result = df.copy()
        for period in periods:
            result[f'ma{period}'] = result['close'].rolling(window=period).mean()
        return result

    @staticmethod
    def calculate_ema(df: pd.DataFrame, periods: list = [12, 26]) -> pd.DataFrame:
        """
        计算指数移动平均线（EMA）

        Args:
            df: K线数据
            periods: EMA 周期列表

        Returns:
            包含 EMA 指标的 DataFrame
        """
        result = df.copy()
        for period in periods:
            result[f'ema{period}'] = result['close'].ewm(span=period, adjust=False).mean()
        return result

    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> pd.DataFrame:
        """
        计算 MACD 指标

        Args:
            df: K线数据
            fast_period: 快线周期
            slow_period: 慢线周期
            signal_period: 信号线周期

        Returns:
            包含 MACD 指标的 DataFrame (macd, signal, hist)
        """
        result = df.copy()

        # 计算 EMA
        ema_fast = result['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = result['close'].ewm(span=slow_period, adjust=False).mean()

        # MACD 线 = 快线 - 慢线
        result['macd'] = ema_fast - ema_slow

        # 信号线 = MACD 的 EMA
        result['macd_signal'] = result['macd'].ewm(span=signal_period, adjust=False).mean()

        # MACD 柱状图 = MACD - 信号线
        result['macd_hist'] = result['macd'] - result['macd_signal']

        return result

    @staticmethod
    def calculate_kdj(
        df: pd.DataFrame,
        n: int = 9,
        m1: int = 3,
        m2: int = 3
    ) -> pd.DataFrame:
        """
        计算 KDJ 指标

        Args:
            df: K线数据，必须包含 high, low, close 列
            n: RSV 周期
            m1: K 值平滑周期
            m2: D 值平滑周期

        Returns:
            包含 KDJ 指标的 DataFrame (k, d, j)
        """
        result = df.copy()

        # 计算 RSV (未成熟随机值)
        low_n = result['low'].rolling(window=n).min()
        high_n = result['high'].rolling(window=n).max()
        rsv = (result['close'] - low_n) / (high_n - low_n) * 100

        # K 值 = RSV 的移动平均
        result['k'] = rsv.ewm(com=m1-1, adjust=False).mean()

        # D 值 = K 值的移动平均
        result['d'] = result['k'].ewm(com=m2-1, adjust=False).mean()

        # J 值 = 3K - 2D
        result['j'] = 3 * result['k'] - 2 * result['d']

        return result

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算 RSI 相对强弱指标

        Args:
            df: K线数据
            period: 周期

        Returns:
            包含 RSI 指标的 DataFrame
        """
        result = df.copy()

        # 计算价格变化
        delta = result['close'].diff()

        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 计算平均涨幅和跌幅
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()

        # 计算 RS 和 RSI
        rs = avg_gain / avg_loss
        result[f'rsi{period}'] = 100 - (100 / (1 + rs))

        return result

    @staticmethod
    def calculate_boll(
        df: pd.DataFrame,
        period: int = 20,
        std_multiplier: float = 2.0
    ) -> pd.DataFrame:
        """
        计算布林带指标

        Args:
            df: K线数据
            period: 周期
            std_multiplier: 标准差倍数

        Returns:
            包含布林带指标的 DataFrame (boll_upper, boll_middle, boll_lower)
        """
        result = df.copy()

        # 中轨 = MA
        result['boll_middle'] = result['close'].rolling(window=period).mean()

        # 标准差
        std = result['close'].rolling(window=period).std()

        # 上轨 = 中轨 + n倍标准差
        result['boll_upper'] = result['boll_middle'] + std_multiplier * std

        # 下轨 = 中轨 - n倍标准差
        result['boll_lower'] = result['boll_middle'] - std_multiplier * std

        return result

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算 ATR 平均真实波幅

        Args:
            df: K线数据，必须包含 high, low, close 列
            period: 周期

        Returns:
            包含 ATR 指标的 DataFrame
        """
        result = df.copy()

        # 计算真实波幅 TR
        high_low = result['high'] - result['low']
        high_close = abs(result['high'] - result['close'].shift(1))
        low_close = abs(result['low'] - result['close'].shift(1))

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        # ATR = TR 的移动平均
        result[f'atr{period}'] = tr.rolling(window=period).mean()

        return result

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有常用技术指标

        Args:
            df: K线数据

        Returns:
            包含所有指标的 DataFrame
        """
        result = df.copy()

        try:
            result = IndicatorCalculator.calculate_ma(result)
            result = IndicatorCalculator.calculate_ema(result)
            result = IndicatorCalculator.calculate_macd(result)
            result = IndicatorCalculator.calculate_kdj(result)
            result = IndicatorCalculator.calculate_rsi(result)
            result = IndicatorCalculator.calculate_boll(result)
            result = IndicatorCalculator.calculate_atr(result)

            logger.info(f"成功计算所有技术指标，数据行数: {len(result)}")
        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")

        return result


# 全局计算器实例
indicator_calculator = IndicatorCalculator()
