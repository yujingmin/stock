"""
简化的 akshare 测试（避免 Unicode 问题）
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from app.services.market_data.akshare_client import AkShareClient

async def test_quote():
    client = AkShareClient()
    try:
        quote = await client.get_stock_realtime_quote("000001")
        print(json.dumps(quote, indent=2, ensure_ascii=False))
        print("\nQuote test: PASS")
        return True
    except Exception as e:
        print(f"Quote test: FAIL - {e}")
        return False

async def test_kline():
    client = AkShareClient()
    try:
        df = await client.get_stock_hist_kline("000001", period="daily")
        print(f"\nKline rows: {len(df)}")
        print(f"Columns: {df.columns.tolist()}")
        print(f"\nLast 3 rows:")
        print(df.tail(3).to_dict('records'))
        print("\nKline test: PASS")
        return True
    except Exception as e:
        print(f"Kline test: FAIL - {e}")
        return False

async def main():
    r1 = await test_quote()
    r2 = await test_kline()
    print(f"\n{'ALL TESTS PASSED' if r1 and r2 else 'SOME TESTS FAILED'}")
    return 0 if r1 and r2 else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
