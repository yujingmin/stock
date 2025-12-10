"""
回测相关 API endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import uuid
from datetime import datetime

from ....schemas.backtesting import (
    BacktestConfig,
    BacktestResult,
    BacktestTask,
    BacktestStatus,
    PerformanceMetrics,
    TradingRecord,
)
from ....services.backtesting.engine import (
    BacktestEngine,
    SimpleMovingAverageStrategy,
    run_multi_strategy_backtest,
)
from ....services.backtesting.optimizer import ParameterOptimizer
from ....services.market_data.akshare_client import akshare_client
from ....services.notification_service import get_notification_service
from ....schemas.notification import NotificationCreate
from ....models.notification import NotificationType, NotificationPriority
from ....core.database import get_mongodb
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 存储回测任务（生产环境应使用数据库）
backtest_tasks = {}


async def run_backtest_task(task_id: str, config: BacktestConfig):
    """
    异步执行回测任务

    Args:
        task_id: 任务ID
        config: 回测配置
    """
    try:
        # 更新任务状态
        backtest_tasks[task_id]["status"] = BacktestStatus.RUNNING
        backtest_tasks[task_id]["updated_at"] = datetime.now()

        logger.info(f"开始执行回测任务 {task_id}, 股票: {config.symbol}")

        # 获取K线数据
        kline_data = await akshare_client.get_stock_hist_kline(
            symbol=config.symbol,
            period=config.period,
            start_date=config.start_date,
            end_date=config.end_date,
            adjust='qfq'
        )

        if kline_data.empty:
            raise ValueError(f"未找到股票 {config.symbol} 的K线数据")

        # 初始化回测引擎
        engine = BacktestEngine()
        engine.setup(
            initial_cash=config.initial_cash,
            commission=config.commission,
            stamp_duty=config.stamp_duty,
            min_commission=config.min_commission,
            slippage=config.slippage,
            enable_t1=True,
            enable_price_limit=True,
        )

        # 添加数据
        engine.add_data(kline_data, name=config.symbol)

        # 添加策略
        strategy_params = config.strategy.strategy_params
        if config.strategy.strategy_type == "simple_ma":
            engine.add_strategy(SimpleMovingAverageStrategy, **strategy_params)
        else:
            raise ValueError(f"不支持的策略类型: {config.strategy.strategy_type}")

        # 运行回测
        result = engine.run()

        # 构造绩效指标
        metrics = PerformanceMetrics(
            initial_value=result['initial_value'],
            final_value=result['final_value'],
            total_return=result['total_return'],
            annual_return=result['annual_return'],
            sharpe_ratio=result['sharpe_ratio'],
            max_drawdown=result['max_drawdown'],
            total_trades=result['total_trades'],
            won_trades=result['won_trades'],
            lost_trades=result['lost_trades'],
            win_rate=result['win_rate'],
        )

        # 转换交易记录
        trading_records = [TradingRecord(**record) for record in result.get('trading_records', [])]

        # 构造回测结果
        backtest_result = BacktestResult(
            task_id=task_id,
            config=config,
            metrics=metrics,
            trading_records=trading_records,
            created_at=datetime.now(),
        )

        # 更新任务状态
        backtest_tasks[task_id]["status"] = BacktestStatus.COMPLETED
        backtest_tasks[task_id]["result"] = backtest_result.dict()
        backtest_tasks[task_id]["updated_at"] = datetime.now()

        logger.info(f"回测任务 {task_id} 完成，总收益率: {metrics.total_return*100:.2f}%")

        # 保存到MongoDB
        try:
            mongo_db = get_mongodb()
            await mongo_db.backtest_results.insert_one({
                "task_id": task_id,
                "symbol": config.symbol,
                "strategy_type": config.strategy.strategy_type,
                "config": config.dict(),
                "metrics": metrics.dict(),
                "trading_records": [record.dict() for record in trading_records],
                "equity_curve": result.get('equity_curve', []),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            })
            logger.info(f"回测结果已保存到MongoDB: {task_id}")

            # 创建回测完成通知
            try:
                notification_service = get_notification_service(mongo_db)
                notification_data = NotificationCreate(
                    type=NotificationType.BACKTEST_COMPLETE,
                    priority=NotificationPriority.NORMAL,
                    title=f"回测完成 - {config.symbol}",
                    content=(
                        f"标的：{config.symbol}\n"
                        f"策略：{config.strategy.strategy_type}\n"
                        f"总收益率：{metrics.total_return*100:.2f}%\n"
                        f"年化收益：{metrics.annual_return*100:.2f}%\n"
                        f"夏普比率：{metrics.sharpe_ratio:.2f}\n"
                        f"最大回撤：{metrics.max_drawdown*100:.2f}%\n"
                        f"交易次数：{metrics.total_trades}\n"
                        f"胜率：{metrics.win_rate*100:.2f}%\n"
                        f"操作指引：查看详细回测报告"
                    ),
                    target_symbol=config.symbol,
                    task_id=task_id,
                    extra_data={
                        "total_return": metrics.total_return,
                        "sharpe_ratio": metrics.sharpe_ratio,
                        "max_drawdown": metrics.max_drawdown,
                    },
                )
                await notification_service.create_notification(notification_data)
                logger.info(f"回测完成通知已创建: {task_id}")
            except Exception as e:
                logger.error(f"创建回测完成通知失败: {str(e)}")

        except Exception as e:
            logger.error(f"保存到MongoDB失败: {str(e)}")

    except Exception as e:
        logger.error(f"回测任务 {task_id} 失败: {str(e)}", exc_info=True)
        backtest_tasks[task_id]["status"] = BacktestStatus.FAILED
        backtest_tasks[task_id]["error_message"] = str(e)
        backtest_tasks[task_id]["updated_at"] = datetime.now()


@router.post("/run", response_model=BacktestTask, summary="运行回测")
async def run_backtest(
    config: BacktestConfig,
    background_tasks: BackgroundTasks
):
    """
    运行回测任务

    - **symbol**: 股票代码
    - **start_date**: 回测开始日期
    - **end_date**: 回测结束日期
    - **initial_cash**: 初始资金
    - **strategy**: 策略配置

    返回任务ID，可通过 GET /backtesting/task/{task_id} 查询结果
    """
    # 生成任务ID
    task_id = str(uuid.uuid4())

    # 创建任务记录
    task = BacktestTask(
        task_id=task_id,
        status=BacktestStatus.PENDING,
        config=config,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    backtest_tasks[task_id] = task.dict()

    # 添加后台任务
    background_tasks.add_task(run_backtest_task, task_id, config)

    logger.info(f"创建回测任务 {task_id}")

    return task


@router.get("/task/{task_id}", response_model=BacktestTask, summary="查询回测任务")
async def get_backtest_task(task_id: str):
    """
    查询回测任务状态和结果

    - **task_id**: 任务ID
    """
    if task_id not in backtest_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task_data = backtest_tasks[task_id]
    return BacktestTask(**task_data)


@router.get("/tasks", response_model=List[BacktestTask], summary="查询所有回测任务")
async def list_backtest_tasks(
    limit: int = 20,
    offset: int = 0
):
    """
    查询回测任务列表

    - **limit**: 返回数量（默认20）
    - **offset**: 偏移量（默认0）
    """
    tasks = list(backtest_tasks.values())

    # 按创建时间倒序排序
    tasks.sort(key=lambda x: x['created_at'], reverse=True)

    # 分页
    tasks = tasks[offset:offset+limit]

    return [BacktestTask(**task) for task in tasks]


@router.delete("/task/{task_id}", summary="删除回测任务")
async def delete_backtest_task(task_id: str):
    """
    删除回测任务

    - **task_id**: 任务ID
    """
    if task_id not in backtest_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    del backtest_tasks[task_id]

    logger.info(f"删除回测任务 {task_id}")

    return {"message": "删除成功"}


@router.get("/result/{task_id}", response_model=BacktestResult, summary="获取回测结果")
async def get_backtest_result(task_id: str):
    """
    获取回测结果（仅返回已完成的任务结果）

    - **task_id**: 任务ID
    """
    if task_id not in backtest_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = backtest_tasks[task_id]

    if task["status"] != BacktestStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"任务状态为 {task['status']}，无法获取结果"
        )

    if task.get("result") is None:
        raise HTTPException(status_code=404, detail="结果不存在")

    return BacktestResult(**task["result"])


@router.post("/optimize", summary="参数优化")
async def optimize_parameters(
    symbol: str,
    start_date: str,
    end_date: str,
    period: str = "daily",
    param_grid: Dict[str, List[Any]] = None,
    metric: str = "sharpe_ratio"
):
    """
    网格搜索参数优化
    """
    try:
        kline_data = await akshare_client.get_stock_hist_kline(
            symbol=symbol, period=period,
            start_date=start_date, end_date=end_date, adjust='qfq'
        )
        if kline_data.empty:
            raise ValueError(f"未找到股票 {symbol} 的K线数据")
        
        optimizer = ParameterOptimizer()
        result = optimizer.grid_search(
            df=kline_data,
            strategy_class=SimpleMovingAverageStrategy,
            param_grid=param_grid,
            metric=metric
        )
        return {
            "symbol": symbol,
            "best_params": result['best_params'],
            "best_score": result['best_score'],
            "best_metrics": result['best_metrics'],
            "total_combinations": result['total_combinations'],
        }
    except Exception as e:
        logger.error(f"参数优化失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-strategy", summary="策略组合回测")
async def run_multi_strategy(
    symbol: str,
    start_date: str,
    end_date: str,
    strategies: List[Dict[str, Any]],
    period: str = "daily",
    initial_cash: float = 100000.0
):
    """
    运行策略组合回测
    """
    try:
        if len(strategies) < 2:
            raise ValueError("策略组合至少需要2个策略")
        
        kline_data = await akshare_client.get_stock_hist_kline(
            symbol=symbol, period=period,
            start_date=start_date, end_date=end_date, adjust='qfq'
        )
        if kline_data.empty:
            raise ValueError(f"未找到股票 {symbol} 的K线数据")
        
        strategy_configs = [
            {
                'class': SimpleMovingAverageStrategy,
                'params': s.get('params', {}),
                'weight': s.get('weight', 1.0)
            }
            for s in strategies
        ]
        
        result = run_multi_strategy_backtest(
            df=kline_data,
            strategies=strategy_configs,
            initial_cash=initial_cash
        )
        
        return {
            "symbol": symbol,
            "strategy_count": result['strategy_count'],
            "metrics": {
                "total_return": result['total_return'],
                "annual_return": result['annual_return'],
                "sharpe_ratio": result['sharpe_ratio'],
                "max_drawdown": result['max_drawdown'],
                "win_rate": result['win_rate'],
            },
            "strategy_results": [
                {
                    "strategy_name": r['strategy_name'],
                    "weight": r['weight'],
                    "total_return": r['total_return'],
                }
                for r in result['strategy_results']
            ]
        }
    except Exception as e:
        logger.error(f"策略组合回测失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
