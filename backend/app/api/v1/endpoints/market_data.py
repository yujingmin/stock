

@router.post("/screen", summary="筛选股票")
async def screen_stocks(filter: StockScreenFilter = Body(...)):
    """
    根据条件筛选股票

    - **filter**: 筛选条件
      - min_pe: 最小市盈率
      - max_pe: 最大市盈率
      - min_pb: 最小市净率
      - max_pb: 最大市净率
      - min_dividend_yield: 最小股息率(%)
      - min_market_cap: 最小市值（亿元）

    示例条件：市盈率 < 20 且股息率 > 3%
    ```json
    {
        "max_pe": 20,
        "min_dividend_yield": 3
    }
    ```
    """
    try:
        # 转换为字典
        conditions = filter.dict(exclude_none=True)

        if not conditions:
            raise HTTPException(status_code=400, detail="至少需要一个筛选条件")

        # 执行筛选
        results = await screen_service.screen_stocks(conditions)

        return {
            "conditions": conditions,
            "results": results,
            "count": len(results)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"股票筛选失败: {str(e)}")


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
        df = await akshare_client.get_stock_hist_kline(
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
