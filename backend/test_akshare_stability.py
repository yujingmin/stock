"""
测试 akshare 各接口的稳定性
识别哪些接口可以正常使用，哪些接口有问题
"""
import asyncio
import time
from datetime import datetime, timedelta
from app.services.market_data.akshare_client import AkShareClient


class StabilityTester:
    """接口稳定性测试器"""

    def __init__(self):
        self.client = AkShareClient()
        self.results = {}

    async def test_interface(self, name: str, test_func, max_attempts: int = 3):
        """
        测试单个接口的稳定性

        Args:
            name: 接口名称
            test_func: 测试函数
            max_attempts: 最大测试次数

        Returns:
            测试结果
        """
        print(f"\n测试接口: {name}")
        print("-" * 50)

        success_count = 0
        total_time = 0
        errors = []

        for i in range(max_attempts):
            try:
                start = time.time()
                result = await test_func()
                elapsed = time.time() - start

                success_count += 1
                total_time += elapsed

                print(f"  [{i+1}/{max_attempts}] 成功 - 耗时: {elapsed:.2f}秒")

                # 等待1秒再进行下一次测试
                if i < max_attempts - 1:
                    await asyncio.sleep(1)

            except Exception as e:
                error_msg = str(e)[:100]
                errors.append(error_msg)
                print(f"  [{i+1}/{max_attempts}] 失败 - 错误: {error_msg}")

                # 等待2秒再重试
                if i < max_attempts - 1:
                    await asyncio.sleep(2)

        # 计算统计数据
        success_rate = (success_count / max_attempts) * 100
        avg_time = total_time / success_count if success_count > 0 else 0

        result = {
            "name": name,
            "success_count": success_count,
            "total_attempts": max_attempts,
            "success_rate": success_rate,
            "avg_response_time": avg_time,
            "errors": errors,
            "status": self._get_status(success_rate),
        }

        self.results[name] = result

        print(f"\n结果:")
        print(f"  成功率: {success_rate:.1f}% ({success_count}/{max_attempts})")
        print(f"  平均响应时间: {avg_time:.2f}秒")
        print(f"  状态: {result['status']}")

        return result

    def _get_status(self, success_rate: float) -> str:
        """根据成功率判断状态"""
        if success_rate >= 80:
            return "稳定"
        elif success_rate >= 50:
            return "不稳定"
        else:
            return "不可用"

    async def run_all_tests(self):
        """运行所有接口测试"""
        print("=" * 60)
        print("akshare 接口稳定性测试")
        print("=" * 60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"每个接口测试 3 次")

        # 定义所有要测试的接口
        tests = [
            # 1. 股票基础信息接口
            ("股票列表", lambda: self.client.get_stock_list()),

            # 2. 实时行情接口
            ("实时行情-000001", lambda: self.client.get_stock_realtime_quote("000001")),
            ("实时行情-000002", lambda: self.client.get_stock_realtime_quote("000002")),

            # 3. 历史K线接口 (短期数据)
            (
                "历史K线-短期",
                lambda: self.client.get_stock_hist_kline(
                    "000001",
                    start_date=(datetime.now() - timedelta(days=7)).strftime("%Y%m%d"),
                    end_date=datetime.now().strftime("%Y%m%d"),
                ),
            ),

            # 4. 历史K线接口 (长期数据)
            (
                "历史K线-长期",
                lambda: self.client.get_stock_hist_kline(
                    "000001",
                    start_date=(datetime.now() - timedelta(days=365)).strftime("%Y%m%d"),
                    end_date=datetime.now().strftime("%Y%m%d"),
                ),
            ),

            # 5. 股票指标接口
            ("股票指标-000001", lambda: self.client.get_stock_indicators("000001")),
            ("股票指标-600000", lambda: self.client.get_stock_indicators("600000")),

            # 6. 财务报表接口
            (
                "财务报表-资产负债表",
                lambda: self.client.get_stock_financial_report("000001", "balance_sheet"),
            ),
            (
                "财务报表-利润表",
                lambda: self.client.get_stock_financial_report("000001", "income_statement"),
            ),

            # 7. 宏观经济数据接口
            ("宏观数据-CPI", lambda: self.client.get_macro_indicator("cpi")),
            ("宏观数据-GDP", lambda: self.client.get_macro_indicator("gdp")),
        ]

        # 执行所有测试
        for name, test_func in tests:
            await self.test_interface(name, test_func)

            # 测试之间暂停3秒，避免请求过于频繁
            await asyncio.sleep(3)

        # 生成报告
        self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("测试报告汇总")
        print("=" * 60)

        # 按状态分类
        stable = []
        unstable = []
        unavailable = []

        for name, result in self.results.items():
            if result["status"] == "稳定":
                stable.append(result)
            elif result["status"] == "不稳定":
                unstable.append(result)
            else:
                unavailable.append(result)

        # 打印稳定接口
        print("\n【稳定接口】(成功率 >= 80%)")
        print("-" * 60)
        if stable:
            for r in sorted(stable, key=lambda x: x["success_rate"], reverse=True):
                print(
                    f"  OK  {r['name']:25} | 成功率: {r['success_rate']:5.1f}% | "
                    f"响应: {r['avg_response_time']:5.2f}秒"
                )
        else:
            print("  (无)")

        # 打印不稳定接口
        print("\n【不稳定接口】(成功率 50-80%)")
        print("-" * 60)
        if unstable:
            for r in sorted(unstable, key=lambda x: x["success_rate"], reverse=True):
                print(
                    f"  WARN {r['name']:25} | 成功率: {r['success_rate']:5.1f}% | "
                    f"响应: {r['avg_response_time']:5.2f}秒"
                )
        else:
            print("  (无)")

        # 打印不可用接口
        print("\n【不可用接口】(成功率 < 50%)")
        print("-" * 60)
        if unavailable:
            for r in sorted(unavailable, key=lambda x: x["success_rate"], reverse=True):
                print(
                    f"  FAIL {r['name']:25} | 成功率: {r['success_rate']:5.1f}% | "
                    f"常见错误: {r['errors'][0][:40] if r['errors'] else 'N/A'}"
                )
        else:
            print("  (无)")

        # 统计摘要
        total = len(self.results)
        print("\n" + "=" * 60)
        print("统计摘要")
        print("=" * 60)
        print(f"总接口数: {total}")
        print(f"稳定接口: {len(stable)} ({len(stable)/total*100:.1f}%)")
        print(f"不稳定接口: {len(unstable)} ({len(unstable)/total*100:.1f}%)")
        print(f"不可用接口: {len(unavailable)} ({len(unavailable)/total*100:.1f}%)")

        # 建议
        print("\n" + "=" * 60)
        print("优化建议")
        print("=" * 60)

        if stable:
            print("\n1. 优先使用稳定接口:")
            for r in stable[:5]:
                print(f"   - {r['name']}")

        if unstable or unavailable:
            print("\n2. 对以下接口增加缓存和降级策略:")
            for r in (unstable + unavailable)[:5]:
                print(f"   - {r['name']}")

        if unavailable:
            print("\n3. 考虑为不可用接口寻找替代方案:")
            for r in unavailable[:3]:
                print(f"   - {r['name']}")


async def main():
    tester = StabilityTester()
    await tester.run_all_tests()

    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
