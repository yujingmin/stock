"""
测试 akshare 修复后的代码
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

from app.services.market_data.akshare_client import AkShareClient

async def test_realtime_quote():
    """测试实时行情获取"""
    client = AkShareClient()

    try:
        print("正在测试实时行情获取...")
        quote = await client.get_stock_realtime_quote("000001")

        print("\n=== 实时行情数据 ===")
        print(f"股票代码: {quote['symbol']}")
        print(f"股票名称: {quote['name']}")
        print(f"最新价: {quote['price']}")
        print(f"涨跌幅: {quote['change_percent']}%")
        print(f"涨跌额: {quote['change_amount']}")
        print(f"成交量: {quote['volume']}")
        print(f"成交额: {quote['amount']}")
        print(f"最高价: {quote['high']}")
        print(f"最低价: {quote['low']}")
        print(f"开盘价: {quote['open']}")
        print(f"昨收价: {quote['close_yesterday']}")

        # 检查是否有 NaN 或 Infinity
        for key, value in quote.items():
            if isinstance(value, float):
                if value != value:  # NaN check
                    print(f"警告: {key} 值为 NaN")
                    return False
                if value == float('inf') or value == float('-inf'):
                    print(f"警告: {key} 值为 Infinity")
                    return False

        print("\n✓ 测试通过：所有数值有效")
        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_kline():
    """测试K线数据获取"""
    client = AkShareClient()

    try:
        print("\n正在测试K线数据获取...")
        df = await client.get_stock_hist_kline("000001", period="daily")

        print(f"\n=== K线数据 ===")
        print(f"数据行数: {len(df)}")
        print(f"数据列: {df.columns.tolist()}")
        print(f"\n最近5天数据:")
        print(df.tail())

        # 检查是否有 NaN 或 Infinity
        if df.isnull().any().any():
            print("警告: 数据中包含 NaN 值")
            print(df.isnull().sum())
            return False

        print("\n✓ 测试通过：K线数据有效")
        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("=" * 50)
    print("AkShare 修复测试")
    print("=" * 50)

    # 测试实时行情
    test1 = await test_realtime_quote()

    # 测试K线数据
    test2 = await test_kline()

    print("\n" + "=" * 50)
    print("测试结果总结")
    print("=" * 50)
    print(f"实时行情测试: {'✓ 通过' if test1 else '✗ 失败'}")
    print(f"K线数据测试: {'✓ 通过' if test2 else '✗ 失败'}")

    if test1 and test2:
        print("\n所有测试通过!")
        return 0
    else:
        print("\n部分测试失败，请检查日志")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
