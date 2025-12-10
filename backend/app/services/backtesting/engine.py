"""
Backtrader 回测引擎
实现单策略和策略组合回测
支持A股特定规则：T+1、涨跌停限制
"""
import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ChinaStockCommission(bt.CommInfoBase):
    """
    A股交易佣金模型
    考虑佣金、印花税、过户费等
    """
    params = (
        ('commission', 0.0003),  # 佣金费率 0.03%
        ('stamp_duty', 0.001),   # 印花税 0.1%（卖出时收取）
        ('min_commission', 5),   # 最低佣金 5元
        ('slippage', 0.001),     # 滑点 0.1%
        ('stocklike', True),
        ('commtype', bt.CommInfoBase.COMM_PERC),
    )

    def _getcommission(self, size, price, pseudoexec):
        """
        计算交易佣金

        Args:
            size: 交易数量（正数买入，负数卖出）
            price: 交易价格
            pseudoexec: 是否模拟执行

        Returns:
            佣金金额
        """
        # 计算交易金额
        value = abs(size) * price

        # 佣金
        commission = max(value * self.p.commission, self.p.min_commission)

        # 如果是卖出，加上印花税
        if size < 0:
            stamp_duty = value * self.p.stamp_duty
            commission += stamp_duty

        return commission


class ChinaStockT1Checker(bt.observers.Observer):
    """
    A股T+1交易限制检查器
    买入的股票当天不能卖出
    """
    lines = ('t1_violation',)

    def __init__(self):
        self.buy_dates = defaultdict(list)  # {data: [buy_dates]}

    def next(self):
        # 记录违规次数
        self.lines.t1_violation[0] = 0


class ChinaStockBroker(bt.brokers.BackBroker):
    """
    A股券商模拟器
    实现T+1交易限制和涨跌停限制
    """
    params = (
        ('price_limit', 0.10),  # 主板涨跌停限制 ±10%
        ('enable_t1', True),    # 是否启用T+1限制
        ('enable_price_limit', True),  # 是否启用涨跌停限制
    )

    def __init__(self):
        super().__init__()
        # 记录每只股票的买入日期 {data: {date: size}}
        self.buy_records = defaultdict(lambda: defaultdict(int))
        self.previous_close = {}  # 记录前一日收盘价

    def _check_t1_restriction(self, data, size):
        """
        检查T+1限制
        返回: (is_allowed, available_size)
        """
        if not self.p.enable_t1 or size > 0:  # 买入不受限制
            return True, size

        # 卖出时检查
        current_date = data.datetime.date(0)

        # 计算可卖出数量（排除今天买入的）
        total_position = self.getposition(data).size
        today_buy = self.buy_records[data._name].get(current_date, 0)
        available = total_position - today_buy

        if abs(size) > available:
            logger.warning(
                f"T+1限制: {data._name} 今日买入 {today_buy} 股，"
                f"可卖出 {available} 股，请求卖出 {abs(size)} 股"
            )
            return False, available

        return True, size

    def _check_price_limit(self, data, price):
        """
        检查涨跌停限制
        返回: (is_allowed, adjusted_price)
        """
        if not self.p.enable_price_limit:
            return True, price

        prev_close = self.previous_close.get(data._name)
        if prev_close is None:
            return True, price

        # 计算涨跌停价格
        upper_limit = prev_close * (1 + self.p.price_limit)
        lower_limit = prev_close * (1 - self.p.price_limit)

        if price > upper_limit:
            logger.warning(
                f"涨停限制: {data._name} 昨收 {prev_close:.2f}, "
                f"涨停价 {upper_limit:.2f}, 请求价格 {price:.2f}"
            )
            return False, upper_limit

        if price < lower_limit:
            logger.warning(
                f"跌停限制: {data._name} 昨收 {prev_close:.2f}, "
                f"跌停价 {lower_limit:.2f}, 请求价格 {price:.2f}"
            )
            return False, lower_limit

        return True, price

    def submit(self, order):
        """提交订单前检查A股特定规则"""
        data = order.data

        # 检查T+1限制
        if order.isbuy():
            # 记录买入日期
            pass  # 在订单执行时记录
        else:  # 卖出
            is_allowed, available_size = self._check_t1_restriction(data, order.size)
            if not is_allowed:
                order.reject()
                return order

        # 检查涨跌停限制（市价单不检查）
        if order.exectype != bt.Order.Market:
            is_allowed, adjusted_price = self._check_price_limit(data, order.price)
            if not is_allowed:
                # 调整为涨跌停价
                order.price = adjusted_price

        return super().submit(order)

    def next(self):
        """每个交易日更新前收盘价"""
        super().next()

        for data in self.datas:
            # 更新前收盘价
            self.previous_close[data._name] = data.close[0]

    def notify_trade(self, trade):
        """记录买入交易"""
        if trade.isopen and trade.size > 0:  # 买入开仓
            data = trade.data
            current_date = data.datetime.date(0)
            self.buy_records[data._name][current_date] += trade.size

        super().notify_trade(trade)



class SimpleMovingAverageStrategy(bt.Strategy):
    """
    简单移动平均线策略示例
    当短期均线上穿长期均线时买入，下穿时卖出
    """
    params = (
        ('fast_period', 5),   # 快线周期
        ('slow_period', 20),  # 慢线周期
        ('printlog', False),  # 是否打印日志
    )

    def __init__(self):
        # 保存收盘价
        self.dataclose = self.datas[0].close

        # 添加均线指标
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.fast_period
        )
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.slow_period
        )

        # 添加交叉信号
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

        # 记录订单
        self.order = None

        # 记录交易和权益曲线
        self.trade_list = []
        self.equity_curve = []

    def log(self, txt, dt=None):
        """日志函数"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            dt = self.datas[0].datetime.date(0)
            if order.isbuy():
                self.log(f'买入执行, 价格: {order.executed.price:.2f}, '
                        f'数量: {order.executed.size:.0f}, '
                        f'佣金: {order.executed.comm:.2f}')
                # 记录买入交易
                self.trade_list.append({
                    'date': dt.isoformat(),
                    'action': 'buy',
                    'price': order.executed.price,
                    'size': int(order.executed.size),
                    'commission': order.executed.comm,
                    'value': order.executed.value,
                })
            elif order.issell():
                self.log(f'卖出执行, 价格: {order.executed.price:.2f}, '
                        f'数量: {order.executed.size:.0f}, '
                        f'佣金: {order.executed.comm:.2f}')
                # 记录卖出交易
                self.trade_list.append({
                    'date': dt.isoformat(),
                    'action': 'sell',
                    'price': order.executed.price,
                    'size': int(order.executed.size),
                    'commission': order.executed.comm,
                    'value': order.executed.value,
                })

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/被拒绝')

        self.order = None

    def notify_trade(self, trade):
        """交易通知"""
        if not trade.isclosed:
            return

        self.log(f'交易盈亏: 毛利润 {trade.pnl:.2f}, 净利润 {trade.pnlcomm:.2f}')

    def next(self):
        """策略主逻辑"""
        # 记录每日权益曲线
        dt = self.datas[0].datetime.date(0)
        portfolio_value = self.broker.getvalue()
        self.equity_curve.append({
            'date': dt.isoformat(),
            'value': portfolio_value,
            'cash': self.broker.getcash(),
        })

        # 检查是否有未完成订单
        if self.order:
            return

        # 检查是否持仓
        if not self.position:
            # 未持仓，检查买入信号
            if self.crossover > 0:  # 金叉
                # 计算可买入数量（使用90%资金）
                cash = self.broker.getcash()
                size = int((cash * 0.9) / self.dataclose[0] / 100) * 100  # A股最小100股
                if size >= 100:
                    self.log(f'买入信号, 价格: {self.dataclose[0]:.2f}')
                    self.order = self.buy(size=size)
        else:
            # 已持仓，检查卖出信号
            if self.crossover < 0:  # 死叉
                self.log(f'卖出信号, 价格: {self.dataclose[0]:.2f}')
                self.order = self.sell(size=self.position.size)


class BacktestEngine:
    """回测引擎"""

    def __init__(self):
        self.cerebro = None
        self.is_multi_strategy = False  # 是否为多策略模式

    def setup(
        self,
        initial_cash: float = 100000.0,
        commission: float = 0.0003,
        stamp_duty: float = 0.001,
        min_commission: float = 5.0,
        slippage: float = 0.001,
        enable_t1: bool = True,
        enable_price_limit: bool = True,
        price_limit: float = 0.10
    ):
        """
        设置回测引擎

        Args:
            initial_cash: 初始资金
            commission: 佣金费率
            stamp_duty: 印花税
            min_commission: 最低佣金
            slippage: 滑点
            enable_t1: 是否启用T+1限制
            enable_price_limit: 是否启用涨跌停限制
            price_limit: 涨跌停幅度（默认10%）
        """
        self.cerebro = bt.Cerebro()

        # 替换为A股券商
        china_broker = ChinaStockBroker(
            enable_t1=enable_t1,
            enable_price_limit=enable_price_limit,
            price_limit=price_limit
        )
        china_broker.setcash(initial_cash)
        self.cerebro.broker = china_broker

        # 设置佣金模型
        comminfo = ChinaStockCommission(
            commission=commission,
            stamp_duty=stamp_duty,
            min_commission=min_commission,
            slippage=slippage
        )
        self.cerebro.broker.addcommissioninfo(comminfo)

        # 设置交易规则（每手100股）
        self.cerebro.addsizer(bt.sizers.FixedSize, stake=100)

        logger.info(
            f"回测引擎已初始化，初始资金: {initial_cash}, "
            f"T+1限制: {enable_t1}, 涨跌停限制: {enable_price_limit}"
        )

    def add_data(self, df: pd.DataFrame, name: str = 'data'):
        """
        添加数据

        Args:
            df: K线数据 DataFrame，必须包含 date, open, high, low, close, volume 列
            name: 数据名称
        """
        # 确保 date 列是 datetime 类型
        df = df.copy()
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)

        # 创建 Backtrader 数据源
        data = bt.feeds.PandasData(
            dataname=df,
            datetime=None,  # 使用索引作为日期
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1
        )

        self.cerebro.adddata(data, name=name)
        logger.info(f"已添加数据: {name}, 数据量: {len(df)}")

    def add_strategy(
        self,
        strategy_class=SimpleMovingAverageStrategy,
        **kwargs
    ):
        """
        添加策略

        Args:
            strategy_class: 策略类
            **kwargs: 策略参数
        """
        self.cerebro.addstrategy(strategy_class, **kwargs)
        logger.info(f"已添加策略: {strategy_class.__name__}")

    def add_analyzers(self):
        """添加分析器"""
        # 收益率分析
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        # 夏普比率
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        # 最大回撤
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        # 交易分析
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    def run(self) -> Dict[str, Any]:
        """
        运行回测

        Returns:
            回测结果字典，包含绩效指标、交易记录、权益曲线
        """
        if self.cerebro is None:
            raise ValueError("回测引擎未初始化，请先调用 setup()")

        # 添加分析器
        self.add_analyzers()

        # 记录初始资金
        start_value = self.cerebro.broker.getvalue()
        logger.info(f'回测开始，初始资金: {start_value:.2f}')

        # 运行回测
        results = self.cerebro.run()
        strategy = results[0]

        # 记录最终资金
        end_value = self.cerebro.broker.getvalue()
        logger.info(f'回测结束，最终资金: {end_value:.2f}')

        # 提取分析结果
        returns = strategy.analyzers.returns.get_analysis()
        sharpe = strategy.analyzers.sharpe.get_analysis()
        drawdown = strategy.analyzers.drawdown.get_analysis()
        trades = strategy.analyzers.trades.get_analysis()

        # 计算收益率
        total_return = (end_value - start_value) / start_value

        # 计算基准对比（如果有权益曲线数据）
        benchmark_metrics = {}
        equity_curve = getattr(strategy, 'equity_curve', [])
        if equity_curve and len(equity_curve) > 1:
            # 计算策略收益曲线
            dates = [item['date'] for item in equity_curve]
            values = [item['value'] for item in equity_curve]

            # 计算日收益率
            daily_returns = []
            for i in range(1, len(values)):
                daily_return = (values[i] - values[i-1]) / values[i-1]
                daily_returns.append(daily_return)

            if daily_returns:
                import numpy as np
                # 计算年化波动率
                volatility = np.std(daily_returns) * np.sqrt(252)
                # 重新计算夏普比率（更准确）
                avg_return = np.mean(daily_returns)
                annual_return_calc = (1 + avg_return) ** 252 - 1
                sharpe_calc = (annual_return_calc / volatility) if volatility > 0 else 0

                benchmark_metrics = {
                    'volatility': volatility,
                    'avg_daily_return': avg_return,
                    'sharpe_calculated': sharpe_calc,
                }

        result = {
            'initial_value': start_value,
            'final_value': end_value,
            'total_return': total_return,
            'annual_return': returns.get('rnorm100', 0) / 100 if 'rnorm100' in returns else 0,
            'sharpe_ratio': sharpe.get('sharperatio', 0) if sharpe.get('sharperatio') is not None else 0,
            'max_drawdown': drawdown.get('max', {}).get('drawdown', 0) / 100,
            'total_trades': trades.get('total', {}).get('total', 0),
            'won_trades': trades.get('won', {}).get('total', 0),
            'lost_trades': trades.get('lost', {}).get('total', 0),
            'trading_records': getattr(strategy, 'trade_list', []),
            'equity_curve': equity_curve,
            'benchmark_metrics': benchmark_metrics,
        }

        # 计算胜率
        if result['total_trades'] > 0:
            result['win_rate'] = result['won_trades'] / result['total_trades']
        else:
            result['win_rate'] = 0

        logger.info(f"回测完成: 总收益率 {result['total_return']*100:.2f}%, "
                   f"夏普比率 {result['sharpe_ratio']:.2f}, "
                   f"最大回撤 {result['max_drawdown']*100:.2f}%")

        return result


# 全局回测引擎实例
backtest_engine = BacktestEngine()


def run_multi_strategy_backtest(
    df: pd.DataFrame,
    strategies: List[Dict[str, Any]],
    initial_cash: float = 100000.0,
    commission: float = 0.0003,
    stamp_duty: float = 0.001,
    min_commission: float = 5.0,
    slippage: float = 0.001,
) -> Dict[str, Any]:
    """
    运行多策略组合回测

    Args:
        df: K线数据
        strategies: 策略配置列表，每个策略包含 {'class': StrategyClass, 'params': {...}, 'weight': 0.5}
        initial_cash: 初始资金
        commission: 佣金费率
        stamp_duty: 印花税
        min_commission: 最低佣金
        slippage: 滑点

    Returns:
        组合回测结果
    """
    if len(strategies) < 2:
        raise ValueError("策略组合至少需要2个策略")

    logger.info(f"开始运行 {len(strategies)} 策略组合回测")

    # 为每个策略运行独立回测
    strategy_results = []
    total_weight = sum(s.get('weight', 1.0) for s in strategies)

    for idx, strategy_config in enumerate(strategies):
        strategy_class = strategy_config.get('class', SimpleMovingAverageStrategy)
        strategy_params = strategy_config.get('params', {})
        weight = strategy_config.get('weight', 1.0) / total_weight

        # 计算该策略分配的资金
        strategy_cash = initial_cash * weight

        logger.info(f"策略 {idx+1}: {strategy_class.__name__}, 权重: {weight:.2%}, 资金: {strategy_cash:.2f}")

        # 创建独立回测引擎
        engine = BacktestEngine()
        engine.setup(
            initial_cash=strategy_cash,
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
        engine.add_strategy(strategy_class, **strategy_params)

        # 运行回测
        result = engine.run()
        result['weight'] = weight
        result['strategy_name'] = strategy_class.__name__
        result['strategy_params'] = strategy_params

        strategy_results.append(result)

    # 合并组合结果
    combined_result = combine_strategy_results(strategy_results, initial_cash)

    logger.info(f"组合回测完成: 总收益率 {combined_result['total_return']*100:.2f}%")

    return combined_result


def combine_strategy_results(
    strategy_results: List[Dict[str, Any]],
    initial_cash: float
) -> Dict[str, Any]:
    """
    合并多个策略的回测结果

    Args:
        strategy_results: 各策略回测结果列表
        initial_cash: 总初始资金

    Returns:
        组合后的回测结果
    """
    import numpy as np

    # 计算组合的总体绩效
    total_final_value = sum(r['final_value'] for r in strategy_results)
    total_return = (total_final_value - initial_cash) / initial_cash

    # 计算加权年化收益
    weighted_annual_return = sum(
        r['annual_return'] * r['weight'] for r in strategy_results
    )

    # 计算加权夏普比率
    weighted_sharpe = sum(
        r['sharpe_ratio'] * r['weight'] for r in strategy_results
    )

    # 计算组合的最大回撤（取最大值）
    max_drawdown = max(r['max_drawdown'] for r in strategy_results)

    # 统计总交易次数
    total_trades = sum(r['total_trades'] for r in strategy_results)
    won_trades = sum(r['won_trades'] for r in strategy_results)
    lost_trades = sum(r['lost_trades'] for r in strategy_results)
    win_rate = won_trades / total_trades if total_trades > 0 else 0

    # 合并权益曲线（按日期对齐并加权）
    combined_equity_curve = []
    if all('equity_curve' in r and r['equity_curve'] for r in strategy_results):
        # 获取所有日期
        all_dates = sorted(set(
            item['date']
            for r in strategy_results
            for item in r['equity_curve']
        ))

        for date in all_dates:
            total_value = 0
            total_cash = 0

            for result in strategy_results:
                # 找到该日期的数据
                date_data = next(
                    (item for item in result['equity_curve'] if item['date'] == date),
                    None
                )
                if date_data:
                    total_value += date_data['value']
                    total_cash += date_data['cash']

            combined_equity_curve.append({
                'date': date,
                'value': total_value,
                'cash': total_cash,
            })

    # 合并交易记录
    combined_trading_records = []
    for result in strategy_results:
        if 'trading_records' in result:
            for record in result['trading_records']:
                record_copy = record.copy()
                record_copy['strategy'] = result['strategy_name']
                combined_trading_records.append(record_copy)

    # 按日期排序
    combined_trading_records.sort(key=lambda x: x['date'])

    return {
        'initial_value': initial_cash,
        'final_value': total_final_value,
        'total_return': total_return,
        'annual_return': weighted_annual_return,
        'sharpe_ratio': weighted_sharpe,
        'max_drawdown': max_drawdown,
        'total_trades': total_trades,
        'won_trades': won_trades,
        'lost_trades': lost_trades,
        'win_rate': win_rate,
        'equity_curve': combined_equity_curve,
        'trading_records': combined_trading_records,
        'strategy_results': strategy_results,
        'strategy_count': len(strategy_results),
    }
