"""
策略参数优化模块
实现网格搜索和参数调优
"""
import backtrader as bt
import pandas as pd
from typing import Dict, Any, List, Tuple
import logging
from itertools import product

from .engine import BacktestEngine, SimpleMovingAverageStrategy

logger = logging.getLogger(__name__)


class ParameterOptimizer:
    """参数优化器"""

    def __init__(self):
        self.results = []

    def grid_search(
        self,
        df: pd.DataFrame,
        strategy_class=SimpleMovingAverageStrategy,
        param_grid: Dict[str, List[Any]] = None,
        initial_cash: float = 100000.0,
        commission: float = 0.0003,
        stamp_duty: float = 0.001,
        min_commission: float = 5.0,
        slippage: float = 0.001,
        metric: str = 'sharpe_ratio'
    ) -> Dict[str, Any]:
        """
        网格搜索参数优化

        Args:
            df: K线数据
            strategy_class: 策略类
            param_grid: 参数网格，例如 {'fast_period': [5, 10, 15], 'slow_period': [20, 30, 40]}
            initial_cash: 初始资金
            commission: 佣金费率
            stamp_duty: 印花税
            min_commission: 最低佣金
            slippage: 滑点
            metric: 优化目标指标 ('sharpe_ratio', 'total_return', 'win_rate')

        Returns:
            最优参数组合和回测结果
        """
        if param_grid is None:
            param_grid = {
                'fast_period': [5, 10, 15, 20],
                'slow_period': [20, 30, 40, 60]
            }

        logger.info(f"开始网格搜索参数优化，参数空间: {param_grid}")

        # 生成所有参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        param_combinations = list(product(*param_values))

        logger.info(f"总共 {len(param_combinations)} 种参数组合")

        self.results = []
        best_result = None
        best_score = float('-inf')

        for idx, params in enumerate(param_combinations):
            # 构造参数字典
            param_dict = dict(zip(param_names, params))

            # 检查参数合理性（快线必须小于慢线）
            if 'fast_period' in param_dict and 'slow_period' in param_dict:
                if param_dict['fast_period'] >= param_dict['slow_period']:
                    logger.debug(f"跳过不合理参数组合: {param_dict}")
                    continue

            try:
                # 创建回测引擎
                engine = BacktestEngine()
                engine.setup(
                    initial_cash=initial_cash,
                    commission=commission,
                    stamp_duty=stamp_duty,
                    min_commission=min_commission,
                    slippage=slippage,
                    enable_t1=True,
                    enable_price_limit=True,
                )

                # 添加数据
                engine.add_data(df.copy(), name='data')

                # 添加策略
                engine.add_strategy(strategy_class, **param_dict)

                # 运行回测
                result = engine.run()

                # 保存结果
                result_record = {
                    'params': param_dict,
                    'total_return': result['total_return'],
                    'annual_return': result['annual_return'],
                    'sharpe_ratio': result['sharpe_ratio'],
                    'max_drawdown': result['max_drawdown'],
                    'total_trades': result['total_trades'],
                    'win_rate': result['win_rate'],
                }
                self.results.append(result_record)

                # 获取当前组合的得分
                score = result.get(metric, 0)

                # 更新最优结果
                if score > best_score:
                    best_score = score
                    best_result = {
                        'params': param_dict,
                        'score': score,
                        'metrics': result_record,
                        'full_result': result
                    }

                logger.info(
                    f"[{idx+1}/{len(param_combinations)}] "
                    f"参数: {param_dict}, "
                    f"{metric}: {score:.4f}"
                )

            except Exception as e:
                logger.error(f"参数组合 {param_dict} 回测失败: {str(e)}")
                continue

        if best_result is None:
            raise ValueError("所有参数组合回测均失败")

        logger.info(
            f"参数优化完成！最优参数: {best_result['params']}, "
            f"{metric}: {best_result['score']:.4f}"
        )

        return {
            'best_params': best_result['params'],
            'best_score': best_result['score'],
            'best_metrics': best_result['metrics'],
            'best_result': best_result['full_result'],
            'all_results': self.results,
            'total_combinations': len(param_combinations),
            'successful_combinations': len(self.results),
        }

    def get_results_dataframe(self) -> pd.DataFrame:
        """
        获取所有优化结果的DataFrame

        Returns:
            包含所有参数组合和性能指标的DataFrame
        """
        if not self.results:
            return pd.DataFrame()

        # 展开参数字典
        records = []
        for result in self.results:
            record = result['params'].copy()
            record.update({
                'total_return': result['total_return'],
                'annual_return': result['annual_return'],
                'sharpe_ratio': result['sharpe_ratio'],
                'max_drawdown': result['max_drawdown'],
                'total_trades': result['total_trades'],
                'win_rate': result['win_rate'],
            })
            records.append(record)

        return pd.DataFrame(records)


# 全局优化器实例
parameter_optimizer = ParameterOptimizer()
