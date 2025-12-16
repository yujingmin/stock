"""
Backtrader 策略模板库
"""

# 简单移动平均线多头策略模板
SMA_LONG_STRATEGY = '''"""
简单移动平均线多头策略

策略逻辑：
- 当短期均线上穿长期均线时买入
- 当短期均线下穿长期均线时卖出
"""
import backtrader as bt


class SMALongStrategy(bt.Strategy):
    params = (
        ('short_period', 10),  # 短期均线周期
        ('long_period', 30),   # 长期均线周期
        ('stake', 100),        # 每次交易股数
    )

    def __init__(self):
        # 计算移动平均线
        self.sma_short = bt.indicators.SMA(self.data.close, period=self.params.short_period)
        self.sma_long = bt.indicators.SMA(self.data.close, period=self.params.long_period)

        # 金叉死叉信号
        self.crossover = bt.indicators.CrossOver(self.sma_short, self.sma_long)

    def next(self):
        # 如果没有持仓
        if not self.position:
            # 金叉买入
            if self.crossover > 0:
                self.buy(size=self.params.stake)

        # 如果有持仓
        else:
            # 死叉卖出
            if self.crossover < 0:
                self.close()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入: 价格={order.executed.price:.2f}, 数量={order.executed.size}')
            elif order.issell():
                self.log(f'卖出: 价格={order.executed.price:.2f}, 数量={order.executed.size}')

    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')
'''

# 网格交易策略模板
GRID_STRATEGY = '''"""
网格交易策略

策略逻辑：
- 在价格区间内设置多个网格
- 价格下跌时逐步买入
- 价格上涨时逐步卖出
"""
import backtrader as bt


class GridStrategy(bt.Strategy):
    params = (
        ('grid_num', 5),         # 网格数量
        ('price_min', 10.0),     # 价格下限
        ('price_max', 15.0),     # 价格上限
        ('stake_per_grid', 100), # 每格交易股数
    )

    def __init__(self):
        # 计算网格价格
        self.grid_prices = []
        step = (self.params.price_max - self.params.price_min) / self.params.grid_num
        for i in range(self.params.grid_num + 1):
            self.grid_prices.append(self.params.price_min + i * step)

        self.last_price = None

    def next(self):
        current_price = self.data.close[0]

        # 首次执行
        if self.last_price is None:
            self.last_price = current_price
            return

        # 遍历网格
        for i, grid_price in enumerate(self.grid_prices):
            # 价格向下穿越网格线 - 买入
            if self.last_price > grid_price >= current_price:
                if self.broker.get_cash() > current_price * self.params.stake_per_grid:
                    self.buy(size=self.params.stake_per_grid)
                    self.log(f'网格买入 @ {grid_price:.2f}')

            # 价格向上穿越网格线 - 卖出
            elif self.last_price < grid_price <= current_price:
                if self.position.size >= self.params.stake_per_grid:
                    self.sell(size=self.params.stake_per_grid)
                    self.log(f'网格卖出 @ {grid_price:.2f}')

        self.last_price = current_price

    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')
'''

# CTA趋势策略模板
CTA_TREND_STRATEGY = '''"""
CTA趋势跟踪策略

策略逻辑：
- 使用ATR计算波动率
- 使用布林带判断趋势
- 趋势突破时开仓，回调时平仓
"""
import backtrader as bt


class CTATrendStrategy(bt.Strategy):
    params = (
        ('bb_period', 20),      # 布林带周期
        ('bb_dev', 2.0),        # 布林带标准差倍数
        ('atr_period', 14),     # ATR周期
        ('atr_mult', 2.0),      # ATR止损倍数
        ('stake', 100),         # 交易股数
    )

    def __init__(self):
        # 布林带指标
        self.bb = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.bb_period,
            devfactor=self.params.bb_dev
        )

        # ATR指标
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)

        # 记录开仓价格
        self.entry_price = None

    def next(self):
        # 如果没有持仓
        if not self.position:
            # 价格突破上轨 - 做多
            if self.data.close[0] > self.bb.top[0]:
                self.buy(size=self.params.stake)
                self.entry_price = self.data.close[0]
                self.log(f'趋势做多 @ {self.entry_price:.2f}')

        # 如果有持仓
        else:
            # 止损条件：价格跌破ATR止损线
            stop_loss = self.entry_price - self.atr[0] * self.params.atr_mult

            # 止盈条件：价格跌破中轨
            if self.data.close[0] < stop_loss:
                self.close()
                self.log(f'止损平仓 @ {self.data.close[0]:.2f}')
            elif self.data.close[0] < self.bb.mid[0]:
                self.close()
                self.log(f'止盈平仓 @ {self.data.close[0]:.2f}')

    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')
'''

# 均值回归策略模板
MEAN_REVERSION_STRATEGY = '''"""
均值回归策略

策略逻辑：
- 使用RSI判断超买超卖
- 超卖时买入，超买时卖出
- 适合震荡市场
"""
import backtrader as bt


class MeanReversionStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),     # RSI周期
        ('rsi_oversold', 30),   # 超卖阈值
        ('rsi_overbought', 70), # 超买阈值
        ('stake', 100),         # 交易股数
    )

    def __init__(self):
        # RSI指标
        self.rsi = bt.indicators.RSI(
            self.data.close,
            period=self.params.rsi_period
        )

    def next(self):
        # 如果没有持仓
        if not self.position:
            # RSI超卖 - 买入
            if self.rsi[0] < self.params.rsi_oversold:
                self.buy(size=self.params.stake)
                self.log(f'超卖买入 RSI={self.rsi[0]:.2f}')

        # 如果有持仓
        else:
            # RSI超买 - 卖出
            if self.rsi[0] > self.params.rsi_overbought:
                self.close()
                self.log(f'超买卖出 RSI={self.rsi[0]:.2f}')

    def log(self, txt):
        dt = self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')
'''

# 模板元数据
TEMPLATE_METADATA = {
    "sma_long": {
        "name": "简单移动平均线多头策略",
        "description": "基于短期和长期移动平均线的金叉死叉信号进行交易，适合趋势明显的市场",
        "code": SMA_LONG_STRATEGY,
        "strategy_type": "趋势跟踪",
        "difficulty": "beginner",
        "risk_level": "low",
        "suitable_markets": ["A股", "港股", "美股"],
        "tags": ["均线", "趋势", "简单"],
        "parameters": {
            "short_period": {
                "type": "int",
                "default": 10,
                "range": [5, 20],
                "description": "短期均线周期"
            },
            "long_period": {
                "type": "int",
                "default": 30,
                "range": [20, 60],
                "description": "长期均线周期"
            },
            "stake": {
                "type": "int",
                "default": 100,
                "description": "每次交易股数"
            }
        }
    },
    "grid": {
        "name": "网格交易策略",
        "description": "在价格区间内设置多个网格，低买高卖，适合震荡市场",
        "code": GRID_STRATEGY,
        "strategy_type": "网格交易",
        "difficulty": "intermediate",
        "risk_level": "medium",
        "suitable_markets": ["A股", "数字货币"],
        "tags": ["网格", "震荡", "套利"],
        "parameters": {
            "grid_num": {
                "type": "int",
                "default": 5,
                "range": [3, 10],
                "description": "网格数量"
            },
            "price_min": {
                "type": "float",
                "description": "价格下限"
            },
            "price_max": {
                "type": "float",
                "description": "价格上限"
            },
            "stake_per_grid": {
                "type": "int",
                "default": 100,
                "description": "每格交易股数"
            }
        }
    },
    "cta_trend": {
        "name": "CTA趋势跟踪策略",
        "description": "使用布林带和ATR进行趋势跟踪，适合趋势明显的商品期货和股指",
        "code": CTA_TREND_STRATEGY,
        "strategy_type": "CTA",
        "difficulty": "advanced",
        "risk_level": "high",
        "suitable_markets": ["期货", "股指"],
        "tags": ["CTA", "趋势", "布林带", "ATR"],
        "parameters": {
            "bb_period": {
                "type": "int",
                "default": 20,
                "range": [10, 30],
                "description": "布林带周期"
            },
            "bb_dev": {
                "type": "float",
                "default": 2.0,
                "range": [1.5, 3.0],
                "description": "布林带标准差倍数"
            },
            "atr_period": {
                "type": "int",
                "default": 14,
                "description": "ATR周期"
            },
            "atr_mult": {
                "type": "float",
                "default": 2.0,
                "description": "ATR止损倍数"
            }
        }
    },
    "mean_reversion": {
        "name": "均值回归策略",
        "description": "使用RSI指标判断超买超卖，适合震荡市场",
        "code": MEAN_REVERSION_STRATEGY,
        "strategy_type": "均值回归",
        "difficulty": "beginner",
        "risk_level": "low",
        "suitable_markets": ["A股", "港股"],
        "tags": ["RSI", "均值回归", "震荡"],
        "parameters": {
            "rsi_period": {
                "type": "int",
                "default": 14,
                "range": [7, 21],
                "description": "RSI周期"
            },
            "rsi_oversold": {
                "type": "int",
                "default": 30,
                "range": [20, 40],
                "description": "超卖阈值"
            },
            "rsi_overbought": {
                "type": "int",
                "default": 70,
                "range": [60, 80],
                "description": "超买阈值"
            }
        }
    }
}
