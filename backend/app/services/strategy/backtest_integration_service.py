"""
回测集成服务 - 连接策略生成和回测执行
"""
import tempfile
import importlib.util
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio
import pandas as pd

from app.services.backtesting.engine import BacktestEngine
from app.services.strategy.strategy_service import strategy_service
from app.services.market_data.hybrid_data_service import hybrid_data_service

logger = logging.getLogger(__name__)


class BacktestIntegrationService:
    """回测集成服务"""

    async def run_strategy_backtest(
        self,
        strategy_id: str,
        user_id: str,
        symbol: str = "000001",  # 股票代码
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_cash: float = 100000.0,
        **backtest_params
    ) -> Dict[str, Any]:
        """
        运行策略回测

        Args:
            strategy_id: 策略版本ID
            user_id: 用户ID
            symbol: 股票代码
            start_date: 开始日期 (格式: YYYYMMDD)
            end_date: 结束日期 (格式: YYYYMMDD)
            initial_cash: 初始资金
            **backtest_params: 其他回测参数

        Returns:
            回测结果
        """
        logger.info(f"开始回测: strategy_id={strategy_id}, symbol={symbol}")

        # 1. 获取策略代码
        strategy = await strategy_service.get_strategy_version(strategy_id, user_id)
        if not strategy:
            raise ValueError("策略不存在")

        strategy_code = strategy["code"]
        strategy_name = strategy["strategy_name"]

        # 2. 动态加载策略类
        try:
            strategy_class = self._load_strategy_class(strategy_code, strategy_name)
        except Exception as e:
            logger.error(f"加载策略类失败: {e}")
            raise ValueError(f"策略代码加载失败: {str(e)}")

        # 3. 获取历史数据
        try:
            df = await self._get_historical_data(symbol, start_date, end_date)
            logger.info(f"获取历史数据成功: {len(df)} 条记录")
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            raise ValueError(f"获取历史数据失败: {str(e)}")

        # 4. 设置回测引擎
        engine = BacktestEngine()
        engine.setup(
            initial_cash=initial_cash,
            commission=backtest_params.get("commission", 0.0003),
            stamp_duty=backtest_params.get("stamp_duty", 0.001),
            min_commission=backtest_params.get("min_commission", 5.0),
            slippage=backtest_params.get("slippage", 0.001),
            enable_t1=backtest_params.get("enable_t1", True),
            enable_price_limit=backtest_params.get("enable_price_limit", True),
        )

        # 5. 添加数据
        engine.add_data(df, name=symbol)

        # 6. 添加策略
        strategy_params = strategy.get("parameters", {})
        engine.add_strategy(strategy_class, **strategy_params)

        # 7. 运行回测
        try:
            result = engine.run()
            logger.info(
                f"回测完成: 收益率={result['total_return']*100:.2f}%, "
                f"夏普比率={result['sharpe_ratio']:.2f}"
            )
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            raise ValueError(f"回测执行失败: {str(e)}")

        # 8. 保存回测结果到策略版本
        performance_metrics = {
            "total_return": result["total_return"],
            "annual_return": result["annual_return"],
            "sharpe_ratio": result["sharpe_ratio"],
            "max_drawdown": result["max_drawdown"],
            "win_rate": result["win_rate"],
            "total_trades": result["total_trades"],
        }

        await strategy_service.link_backtest_result(
            strategy_id=strategy_id,
            user_id=user_id,
            backtest_result_id=None,  # 可以后续保存到MongoDB
            metrics=performance_metrics,
        )

        # 9. 构建完整的回测结果
        backtest_result = {
            "strategy_id": strategy_id,
            "strategy_name": strategy_name,
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "initial_cash": initial_cash,
            "backtest_params": backtest_params,
            "performance": performance_metrics,
            "equity_curve": result["equity_curve"],
            "trading_records": result["trading_records"][:100],  # 限制返回数量
            "total_trades_count": len(result["trading_records"]),
            "created_at": datetime.now().isoformat(),
        }

        logger.info(f"回测结果已保存到策略版本: {strategy_id}")

        return backtest_result

    def _load_strategy_class(self, strategy_code: str, strategy_name: str):
        """
        动态加载策略类

        Args:
            strategy_code: 策略代码
            strategy_name: 策略类名

        Returns:
            策略类对象
        """
        # 创建临时模块
        module_name = f"dynamic_strategy_{datetime.now().timestamp()}"

        # 使用 exec 执行代码
        namespace = {"__name__": module_name}

        # 添加必要的导入
        imports = """
import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
"""
        full_code = imports + "\n" + strategy_code

        try:
            exec(full_code, namespace)
        except Exception as e:
            logger.error(f"执行策略代码失败: {e}")
            raise

        # 查找策略类
        strategy_class = namespace.get(strategy_name)

        if strategy_class is None:
            # 尝试查找任何继承自 bt.Strategy 的类
            import backtrader as bt

            for name, obj in namespace.items():
                if (
                    isinstance(obj, type)
                    and issubclass(obj, bt.Strategy)
                    and obj != bt.Strategy
                ):
                    strategy_class = obj
                    logger.info(f"找到策略类: {name}")
                    break

        if strategy_class is None:
            raise ValueError(f"未找到策略类 {strategy_name} 或任何继承自 bt.Strategy 的类")

        return strategy_class

    async def _get_historical_data(
        self, symbol: str, start_date: Optional[str], end_date: Optional[str]
    ):
        """
        获取历史K线数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        # 设置默认日期范围（最近1年）
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        if not start_date:
            start = datetime.now() - timedelta(days=365)
            start_date = start.strftime("%Y%m%d")

        # 使用混合数据服务获取历史数据
        df = await hybrid_data_service.get_stock_hist_kline(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",  # 前复权
        )

        if df is None or df.empty:
            raise ValueError(f"无法获取股票 {symbol} 的历史数据")

        # hybrid_data_service 已经返回标准化的列名,无需重命名
        # 确保包含所需列
        required_columns = ["date", "open", "high", "low", "close", "volume"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"数据缺少必需列: {col}")

        # 选择需要的列
        df = df[required_columns].copy()

        # 确保数据类型正确
        df["date"] = pd.to_datetime(df["date"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # 删除包含 NaN 的行
        df = df.dropna()

        # 按日期排序
        df = df.sort_values("date").reset_index(drop=True)

        return df

    async def quick_backtest_from_code(
        self,
        strategy_code: str,
        symbol: str = "000001",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_cash: float = 100000.0,
        strategy_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        快速回测（不保存策略版本）

        Args:
            strategy_code: 策略代码
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            initial_cash: 初始资金
            strategy_params: 策略参数

        Returns:
            回测结果
        """
        logger.info(f"快速回测: symbol={symbol}")

        # 1. 动态加载策略类
        try:
            # 从代码中提取策略类名
            import re

            match = re.search(r"class\s+(\w+)\s*\(", strategy_code)
            if not match:
                raise ValueError("无法从代码中提取策略类名")

            strategy_name = match.group(1)
            strategy_class = self._load_strategy_class(strategy_code, strategy_name)
        except Exception as e:
            logger.error(f"加载策略类失败: {e}")
            raise ValueError(f"策略代码加载失败: {str(e)}")

        # 2. 获取历史数据
        try:
            df = await self._get_historical_data(symbol, start_date, end_date)
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            raise ValueError(f"获取历史数据失败: {str(e)}")

        # 3. 设置回测引擎
        engine = BacktestEngine()
        engine.setup(initial_cash=initial_cash)

        # 4. 添加数据和策略
        engine.add_data(df, name=symbol)
        engine.add_strategy(strategy_class, **(strategy_params or {}))

        # 5. 运行回测
        try:
            result = engine.run()
        except Exception as e:
            logger.error(f"回测执行失败: {e}")
            raise ValueError(f"回测执行失败: {str(e)}")

        # 6. 返回简化结果
        return {
            "performance": {
                "total_return": result["total_return"],
                "annual_return": result["annual_return"],
                "sharpe_ratio": result["sharpe_ratio"],
                "max_drawdown": result["max_drawdown"],
                "win_rate": result["win_rate"],
                "total_trades": result["total_trades"],
            },
            "equity_curve": result["equity_curve"],
            "trading_records": result["trading_records"][:50],
        }


# 全局服务实例
backtest_integration_service = BacktestIntegrationService()
