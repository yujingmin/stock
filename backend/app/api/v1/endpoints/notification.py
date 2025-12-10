"""
通知相关 API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ....schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse,
    NotificationListResponse,
    NotificationQuery,
    NotificationStatResponse,
)
from ....models.notification import NotificationType, NotificationPriority
from ....services.notification_service import get_notification_service
from ....core.database import get_mongodb

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=dict, summary="创建通知")
async def create_notification(
    notification: NotificationCreate,
    db=Depends(get_mongodb)
):
    """
    创建通知

    - **type**: 通知类型 (risk_alert/strategy_signal/backtest_complete等)
    - **priority**: 优先级 (urgent/normal/minor)
    - **title**: 标题
    - **content**: 内容
    """
    try:
        service = get_notification_service(db)
        notification_id = await service.create_notification(notification)
        return {
            "notification_id": notification_id,
            "message": "通知创建成功"
        }
    except Exception as e:
        logger.error(f"创建通知失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=NotificationListResponse, summary="查询通知列表")
async def query_notifications(
    type: Optional[NotificationType] = None,
    priority: Optional[NotificationPriority] = None,
    read_status: Optional[bool] = None,
    target_symbol: Optional[str] = None,
    strategy_id: Optional[str] = None,
    follow_up: Optional[bool] = None,
    limit: int = 20,
    offset: int = 0,
    db=Depends(get_mongodb)
):
    """
    查询通知列表

    - **type**: 通知类型（可选）
    - **priority**: 优先级（可选）
    - **read_status**: 已读状态（可选）
    - **target_symbol**: 股票代码（可选）
    - **strategy_id**: 策略ID（可选）
    - **follow_up**: 仅显示需要跟进的（可选）
    - **limit**: 返回数量（默认20）
    - **offset**: 偏移量（默认0）
    """
    try:
        query = NotificationQuery(
            type=type,
            priority=priority,
            read_status=read_status,
            target_symbol=target_symbol,
            strategy_id=strategy_id,
            follow_up=follow_up,
            limit=limit,
            offset=offset,
        )

        service = get_notification_service(db)
        result = await service.query_notifications(query)

        return NotificationListResponse(
            total=result['total'],
            unread_count=result['unread_count'],
            notifications=[
                NotificationResponse(**notif)
                for notif in result['notifications']
            ]
        )
    except Exception as e:
        logger.error(f"查询通知列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notification_id}", response_model=NotificationResponse, summary="获取通知详情")
async def get_notification(
    notification_id: str,
    db=Depends(get_mongodb)
):
    """
    获取通知详情

    - **notification_id**: 通知ID
    """
    try:
        service = get_notification_service(db)
        notification = await service.get_notification(notification_id)

        if not notification:
            raise HTTPException(status_code=404, detail="通知不存在")

        return NotificationResponse(**notification)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取通知详情失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{notification_id}", response_model=dict, summary="更新通知")
async def update_notification(
    notification_id: str,
    update_data: NotificationUpdate,
    db=Depends(get_mongodb)
):
    """
    更新通知

    - **notification_id**: 通知ID
    - **read_status**: 已读状态（可选）
    - **follow_up**: 是否需要跟进（可选）
    - **follow_up_time**: 跟进提醒时间（可选）
    """
    try:
        service = get_notification_service(db)
        success = await service.update_notification(notification_id, update_data)

        if not success:
            raise HTTPException(status_code=404, detail="通知不存在或更新失败")

        return {"message": "更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新通知失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/read", response_model=dict, summary="标记为已读")
async def mark_as_read(
    notification_id: str,
    db=Depends(get_mongodb)
):
    """
    标记为已读

    - **notification_id**: 通知ID
    """
    try:
        service = get_notification_service(db)
        success = await service.mark_as_read(notification_id)

        if not success:
            raise HTTPException(status_code=404, detail="通知不存在")

        return {"message": "已标记为已读"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记已读失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/read-all", response_model=dict, summary="全部标记为已读")
async def mark_all_as_read(
    db=Depends(get_mongodb)
):
    """
    全部标记为已读
    """
    try:
        service = get_notification_service(db)
        count = await service.mark_all_as_read()

        return {
            "message": f"已标记 {count} 条通知为已读",
            "count": count
        }
    except Exception as e:
        logger.error(f"全部标记已读失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}", response_model=dict, summary="删除通知")
async def delete_notification(
    notification_id: str,
    db=Depends(get_mongodb)
):
    """
    删除通知

    - **notification_id**: 通知ID
    """
    try:
        service = get_notification_service(db)
        success = await service.delete_notification(notification_id)

        if not success:
            raise HTTPException(status_code=404, detail="通知不存在")

        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除通知失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-message", response_model=dict, summary="生成结构化消息")
async def generate_message(
    type: NotificationType,
    data: dict,
    db=Depends(get_mongodb)
):
    """
    生成结构化消息内容

    - **type**: 通知类型
    - **data**: 消息参数
    """
    try:
        service = get_notification_service(db)
        message = await service.generate_structured_message(type, **data)
        return message
    except Exception as e:
        logger.error(f"生成消息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=NotificationStatResponse, summary="通知统计分析")
async def get_notification_stats(
    period: str = "monthly",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db=Depends(get_mongodb)
):
    """
    获取通知统计分析

    - **period**: 统计周期 (daily/weekly/monthly)
    - **start_date**: 开始日期 (可选，格式: YYYY-MM-DD)
    - **end_date**: 结束日期 (可选，格式: YYYY-MM-DD)
    """
    try:
        # 解析日期范围
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            # 默认最近30天
            start_dt = datetime.now() - timedelta(days=30)

        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()

        # 查询统计数据
        service = get_notification_service(db)
        collection = service.collection

        # 时间范围过滤
        time_filter = {
            "created_at": {
                "$gte": start_dt,
                "$lte": end_dt
            }
        }

        # 总通知数
        total_notifications = await collection.count_documents(time_filter)

        # 按优先级统计
        urgent_count = await collection.count_documents({
            **time_filter,
            "priority": NotificationPriority.URGENT
        })
        normal_count = await collection.count_documents({
            **time_filter,
            "priority": NotificationPriority.NORMAL
        })
        minor_count = await collection.count_documents({
            **time_filter,
            "priority": NotificationPriority.MINOR
        })

        # 按类型统计
        type_distribution = {}
        for ntype in NotificationType:
            count = await collection.count_documents({
                **time_filter,
                "type": ntype.value
            })
            if count > 0:
                type_distribution[ntype.value] = count

        # 推送统计
        pushed_count = await collection.count_documents({
            **time_filter,
            "pushed": True
        })
        read_count = await collection.count_documents({
            **time_filter,
            "read_status": True
        })

        # 计算平均阅读时间
        avg_read_time = None
        read_notifications = await collection.find({
            **time_filter,
            "read_status": True,
            "read_at": {"$exists": True}
        }).to_list(length=None)

        if read_notifications:
            read_times = []
            for notif in read_notifications:
                if notif.get("read_at") and notif.get("created_at"):
                    delta = (notif["read_at"] - notif["created_at"]).total_seconds()
                    read_times.append(delta)
            if read_times:
                avg_read_time = sum(read_times) / len(read_times)

        # 触发最多的股票
        most_triggered_symbol = None
        symbol_pipeline = [
            {"$match": {**time_filter, "target_symbol": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$target_symbol", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]
        symbol_result = await collection.aggregate(symbol_pipeline).to_list(length=1)
        if symbol_result:
            most_triggered_symbol = symbol_result[0]["_id"]

        # 触发最多的策略
        most_triggered_strategy = None
        strategy_pipeline = [
            {"$match": {**time_filter, "strategy_id": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$strategy_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 1}
        ]
        strategy_result = await collection.aggregate(strategy_pipeline).to_list(length=1)
        if strategy_result:
            most_triggered_strategy = strategy_result[0]["_id"]

        return NotificationStatResponse(
            period=period,
            start_date=start_dt,
            end_date=end_dt,
            total_notifications=total_notifications,
            urgent_count=urgent_count,
            normal_count=normal_count,
            minor_count=minor_count,
            type_distribution=type_distribution,
            pushed_count=pushed_count,
            read_count=read_count,
            avg_read_time=avg_read_time,
            most_triggered_symbol=most_triggered_symbol,
            most_triggered_strategy=most_triggered_strategy,
        )

    except Exception as e:
        logger.error(f"获取统计分析失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", summary="导出通知日志")
async def export_notifications(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    format: str = "json",
    db=Depends(get_mongodb)
):
    """
    导出通知日志

    - **start_date**: 开始日期 (可选，格式: YYYY-MM-DD)
    - **end_date**: 结束日期 (可选，格式: YYYY-MM-DD)
    - **format**: 导出格式 (json/csv，默认json)
    """
    try:
        # 解析日期范围
        time_filter = {}
        if start_date or end_date:
            time_filter["created_at"] = {}
            if start_date:
                time_filter["created_at"]["$gte"] = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                time_filter["created_at"]["$lte"] = datetime.strptime(end_date, "%Y-%m-%d")

        service = get_notification_service(db)
        collection = service.collection

        # 查询所有通知
        notifications = await collection.find(time_filter).sort("created_at", -1).to_list(length=None)

        if format == "csv":
            # CSV格式导出（简化版）
            import csv
            import io
            from fastapi.responses import StreamingResponse

            output = io.StringIO()
            if notifications:
                fieldnames = ["notification_id", "type", "priority", "title", "target_symbol",
                             "read_status", "created_at"]
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for notif in notifications:
                    writer.writerow({
                        "notification_id": notif.get("notification_id"),
                        "type": notif.get("type"),
                        "priority": notif.get("priority"),
                        "title": notif.get("title"),
                        "target_symbol": notif.get("target_symbol", ""),
                        "read_status": notif.get("read_status"),
                        "created_at": notif.get("created_at").isoformat() if notif.get("created_at") else "",
                    })

            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=notifications.csv"}
            )
        else:
            # JSON格式导出
            # 转换日期为字符串
            for notif in notifications:
                for key in ["created_at", "updated_at", "read_at", "pushed_at", "follow_up_time"]:
                    if key in notif and notif[key]:
                        notif[key] = notif[key].isoformat()
                # 移除MongoDB的_id字段
                notif.pop("_id", None)

            return {
                "total": len(notifications),
                "notifications": notifications
            }

    except Exception as e:
        logger.error(f"导出通知日志失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

