"""
测试混合数据服务
验证根据接口稳定性自动选择数据源
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.services.market_data.hybrid_data_service import hybrid_data_service


async def test_hybrid_service():
    """测试混合数据服务的所有接口"""
    print("=" * 60)
    print("混合数据服务测试")
    print("=" * 60)
    print()

    # 测试 1: 股票列表 (应使用 Mock 数据)
    print("[测试 1] 获取股票列表 (不可用接口 -> Mock 数据)")
    print("-" * 60)
    try:
        stocks = await hybrid_data_service.get_stock_list()
        print(f"[成功] 获取到 {len(stocks)} 只股票")
        print(f"示例: {stocks[0]}")
    except Exception as e:
        print(f"[失败] {str(e)}")
    print()

    # 测试 2: 实时行情 (应使用 Mock 数据)
    print("[测试 2] 获取实时行情 (不可用接口 -> Mock 数据)")
    print("-" * 60)
    try:
        quote = await hybrid_data_service.get_stock_realtime_quote("000001")
        print(f"[成功] 股票: {quote['name']}")
        print(f"  价格: {quote['price']}")
        print(f"  涨跌幅: {quote['change_percent']:.2f}%")
    except Exception as e:
        print(f"[失败] {str(e)}")
    print()

    # 测试 3: 历史K线 (应使用 Mock 数据)
    print("[测试 3] 获取历史K线 (不可用接口 -> Mock 数据)")
    print("-" * 60)
    try:
        df = await hybrid_data_service.get_stock_hist_kline(
            symbol="000001",
            start_date="20231201",
            end_date="20231210"
        )
        print(f"[成功] 获取 {len(df)} 条K线数据")
        print(f"  列: {list(df.columns)}")
        print(f"  示例数据:")
        print(df.head(3))
    except Exception as e:
        print(f"[失败] {str(e)}")
    print()

    # 测试 4: 股票指标 (应使用 Mock 数据)
    print("[测试 4] 获取股票指标 (不可用接口 -> Mock 数据)")
    print("-" * 60)
    try:
        indicators = await hybrid_data_service.get_stock_indicators("000001")
        print(f"[成功] 获取股票指标")
        print(f"  市盈率: {indicators.get('pe_ratio')}")
        print(f"  市净率: {indicators.get('pb_ratio')}")
    except Exception as e:
        print(f"[失败] {str(e)}")
    print()

    # 测试 5: 财务报表 (应尝试使用真实数据,失败则降级)
    print("[测试 5] 获取财务报表 (稳定接口 -> 尝试真实数据)")
    print("-" * 60)
    try:
        df = await hybrid_data_service.get_stock_financial_report(
            symbol="000001",
            report_type="balance_sheet"
        )
        if df.empty:
            print("[警告] 返回空数据 (可能使用了 Mock 降级)")
        else:
            print(f"[成功] 获取财务报表,{len(df)} 行数据")
            print(f"  列: {list(df.columns)[:5]}...")
    except Exception as e:
        print(f"[失败] {str(e)}")
    print()

    # 测试 6: 宏观指标 (应尝试使用真实数据,失败则降级)
    print("[测试 6] 获取宏观指标 (稳定接口 -> 尝试真实数据)")
    print("-" * 60)
    try:
        df = await hybrid_data_service.get_macro_indicator("cpi")
        if df.empty:
            print("[警告] 返回空数据 (可能降级或不支持)")
        else:
            print(f"[成功] 获取 CPI 数据,{len(df)} 行")
            print(f"  列: {list(df.columns)}")
    except Exception as e:
        print(f"[失败] {str(e)}")
    print()

    print("=" * 60)
    print("测试完成!")
    print("=" * 60)
    print()
    print("总结:")
    print("- 不可用接口(股票列表/实时行情/K线/指标): 使用 Mock 数据")
    print("- 稳定接口(财务报表/宏观数据): 尝试真实数据,失败则降级")


if __name__ == "__main__":
    asyncio.run(test_hybrid_service())
