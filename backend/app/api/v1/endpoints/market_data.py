"""
市场数据API端点
"""
import io
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Body, Query
from fastapi.responses import StreamingResponse
import pandas as pd

from app.services.market_data.hybrid_data_service import hybrid_data_service
from app.services.market_data.indicator_calculator import IndicatorCalculator
from app.services.market_data.screen_service import ScreenService
from app.services.market_data.cache_service import MarketDataCacheService

# 创建路由器
router = APIRouter()

# 初始化服务
# 使用混合数据服务 (根据接口稳定性自动选择 akshare 或 mock 数据)
data_service = hybrid_data_service
indicator_calculator = IndicatorCalculator()
screen_service = ScreenService()
cache_service = MarketDataCacheService()


@router.get("/quote/{symbol}", summary="获取股票实时行情")
async def get_stock_quote(symbol: str):
    """
    获取股票实时行情数据

    - **symbol**: 股票代码（如：000001）
    """
    try:
        # 尝试从缓存获取
        cached_data = await cache_service.get_cached_data("realtime_quote", symbol)
        if cached_data:
            return cached_data

        # 从数据服务获取
        quote_data = await data_service.get_stock_realtime_quote(symbol)

        # 缓存数据
        await cache_service.set_cached_data("realtime_quote", symbol, quote_data, ttl=10)

        return quote_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取行情数据失败: {str(e)}")


@router.get("/kline/{symbol}", summary="获取K线数据")
async def get_stock_kline(
    symbol: str,
    period: str = Query("daily", description="周期: daily/weekly/monthly"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYYMMDD"),
    with_indicators: bool = Query(False, description="是否包含技术指标")
):
    """
    获取股票K线历史数据

    - **symbol**: 股票代码
    - **period**: 周期（daily/weekly/monthly）
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **with_indicators**: 是否计算技术指标
    """
    try:
        # 获取K线数据
        df = await data_service.get_stock_hist_kline(
            symbol, period, start_date, end_date
        )

        if df.empty:
            raise HTTPException(status_code=404, detail="未找到K线数据")

        # 计算技术指标
        if with_indicators:
            df = indicator_calculator.calculate_all_indicators(df)

        # 转换为字典列表
        data = df.to_dict('records')

        return {
            "symbol": symbol,
            "period": period,
            "count": len(data),
            "data": data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


@router.get("/indicators/{symbol}", summary="获取股票指标")
async def get_stock_indicators(symbol: str):
    """
    获取股票的财务指标

    - **symbol**: 股票代码
    """
    try:
        indicators = await data_service.get_stock_indicators(symbol)
        return indicators

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票指标失败: {str(e)}")


@router.get("/list", summary="获取股票列表")
async def get_stock_list(
    market: Optional[str] = Query(None, description="市场: 沪A/深A/北A/all")
):
    """
    获取股票列表

    - **market**: 市场代码（可选）
    """
    try:
        stock_list = await data_service.get_stock_list(market)
        return stock_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票列表失败: {str(e)}")


@router.post("/sync/{symbol}", summary="同步历史数据")
async def sync_historical_data(
    symbol: str,
    period: str = Query("daily", description="周期"),
    years: int = Query(10, description="同步年数")
):
    """
    同步股票历史数据到InfluxDB

    - **symbol**: 股票代码
    - **period**: 周期
    - **years**: 同步年数
    """
    try:
        # TODO: 实现数据同步到InfluxDB的逻辑
        return {
            "message": "数据同步功能开发中",
            "symbol": symbol,
            "period": period,
            "years": years
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步历史数据失败: {str(e)}")


@router.post("/screen", summary="筛选股票")
async def screen_stocks(filter: Dict[str, Any] = Body(...)):
    """
    根据条件筛选股票
    """
    try:
        results = await screen_service.screen_stocks(filter)

        return {
            "conditions": filter,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"筛选股票失败: {str(e)}")


@router.post("/screen/rules", summary="保存筛选规则")
async def save_screen_rule(
    name: str = Body(..., description="规则名称"),
    conditions: Dict[str, Any] = Body(..., description="筛选条件"),
    description: Optional[str] = Body(None, description="规则描述")
):
    """
    保存筛选规则以便后续复用

    - **name**: 规则名称
    - **conditions**: 筛选条件字典
    - **description**: 规则描述（可选）
    """
    try:
        rule_id = await screen_service.save_screen_rule(name, conditions, description)

        return {
            "message": "筛选规则已保存",
            "rule_id": rule_id,
            "name": name
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存筛选规则失败: {str(e)}")


@router.get("/screen/rules", summary="获取所有筛选规则")
async def list_screen_rules():
    """
    获取所有已保存的筛选规则列表
    """
    try:
        rules = await screen_service.list_screen_rules()

        return {
            "rules": rules,
            "count": len(rules)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取筛选规则失败: {str(e)}")


@router.get("/screen/rules/{rule_id}", summary="获取筛选规则详情")
async def get_screen_rule(rule_id: str):
    """
    获取指定筛选规则的详情

    - **rule_id**: 规则ID
    """
    try:
        rule = await screen_service.get_screen_rule(rule_id)

        if not rule:
            raise HTTPException(status_code=404, detail="筛选规则不存在")

        return rule

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取筛选规则失败: {str(e)}")


@router.post("/screen/rules/{rule_id}/apply", summary="应用筛选规则")
async def apply_screen_rule(rule_id: str):
    """
    应用已保存的筛选规则进行股票筛选

    - **rule_id**: 规则ID
    """
    try:
        # 获取规则
        rule = await screen_service.get_screen_rule(rule_id)

        if not rule:
            raise HTTPException(status_code=404, detail="筛选规则不存在")

        # 执行筛选
        results = await screen_service.screen_stocks(rule["conditions"])

        return {
            "rule_name": rule["name"],
            "conditions": rule["conditions"],
            "results": results,
            "count": len(results)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"应用筛选规则失败: {str(e)}")


@router.delete("/screen/rules/{rule_id}", summary="删除筛选规则")
async def delete_screen_rule(rule_id: str):
    """
    删除指定的筛选规则

    - **rule_id**: 规则ID
    """
    try:
        success = await screen_service.delete_screen_rule(rule_id)

        if not success:
            raise HTTPException(status_code=404, detail="筛选规则不存在")

        return {
            "message": "筛选规则已删除",
            "rule_id": rule_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除筛选规则失败: {str(e)}")


@router.get("/export/kline/{symbol}", summary="导出K线数据")
async def export_kline_data(
    symbol: str,
    period: str = Query("daily", description="周期"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYYMMDD"),
    format: str = Query("csv", description="导出格式: csv/excel"),
    with_indicators: bool = Query(False, description="是否包含技术指标")
):
    """
    导出股票K线历史数据为 Excel 或 CSV 格式

    - **symbol**: 股票代码
    - **period**: 周期（daily/weekly/monthly）
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    - **format**: 导出格式（csv/excel）
    - **with_indicators**: 是否包含技术指标

    返回文件下载
    """
    try:
        # 获取K线数据
        df = await data_service.get_stock_hist_kline(
            symbol, period, start_date, end_date
        )

        if df.empty:
            raise HTTPException(status_code=404, detail="未找到数据")

        # 计算技术指标
        if with_indicators:
            df = indicator_calculator.calculate_all_indicators(df)

        # 生成文件
        if format == "excel":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='K线数据')
            output.seek(0)

            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename={symbol}_{period}_kline.xlsx"
                }
            )

        else:  # csv
            output = io.StringIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            output.seek(0)

            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={symbol}_{period}_kline.csv"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")


@router.get("/export/screen", summary="导出筛选结果")
async def export_screen_results(
    conditions: str = Query(..., description="筛选条件JSON字符串"),
    format: str = Query("csv", description="导出格式: csv/excel")
):
    """
    导出股票筛选结果为 Excel 或 CSV 格式

    - **conditions**: 筛选条件（JSON字符串）
    - **format**: 导出格式（csv/excel）

    示例: ?conditions={"max_pe":20,"min_dividend_yield":3}&format=excel
    """
    try:
        import json

        # 解析条件
        try:
            cond_dict = json.loads(conditions)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="筛选条件格式错误")

        # 执行筛选
        results = await screen_service.screen_stocks(cond_dict)

        if not results:
            raise HTTPException(status_code=404, detail="未找到符合条件的股票")

        # 转换为 DataFrame
        df = pd.DataFrame(results)

        # 生成文件
        if format == "excel":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='筛选结果')
            output.seek(0)

            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": "attachment; filename=screen_results.xlsx"
                }
            )

        else:  # csv
            output = io.StringIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')
            output.seek(0)

            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": "attachment; filename=screen_results.csv"
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出筛选结果失败: {str(e)}")
