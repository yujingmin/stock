"""
通知服务模块
处理通知的创建、推送和管理
"""
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...models.notification import (
    NotificationModel,
    NotificationPriority,
    NotificationType,
)
from ...schemas.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationQuery,
)

logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.notifications
        self.watchlist_collection = db.watchlist
        self.position_collection = db.positions

    async def check_symbol_monitored(
        self,
        symbol: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        检查股票是否在监控列表中（自选股或持仓）

        Args:
            symbol: 股票代码
            user_id: 用户ID

        Returns:
            是否在监控列表中
        """
        filter_dict = {"symbol": symbol, "enable_notification": True}
        if user_id:
            filter_dict["user_id"] = user_id

        # 检查自选股
        watchlist_count = await self.watchlist_collection.count_documents(filter_dict)
        if watchlist_count > 0:
            return True

        # 检查持仓
        position_count = await self.position_collection.count_documents(filter_dict)
        if position_count > 0:
            return True

        return False

    async def check_notification_frequency(
        self,
        notification_type: NotificationType,
        symbol: Optional[str] = None,
        user_id: Optional[str] = None,
        threshold_minutes: int = 30
    ) -> bool:
        """
        检查通知频率（防止重复推送）

        Args:
            notification_type: 通知类型
            symbol: 股票代码（可选）
            user_id: 用户ID（可选）
            threshold_minutes: 频率阈值（分钟）

        Returns:
            是否允许发送（True表示可以发送）
        """
        # 构建查询条件
        filter_dict = {
            "type": notification_type.value,
            "created_at": {
                "$gte": datetime.now() - timedelta(minutes=threshold_minutes)
            }
        }

        if symbol:
            filter_dict["target_symbol"] = symbol
        if user_id:
            filter_dict["user_id"] = user_id

        # 检查是否存在相同类型的最近通知
        recent_count = await self.collection.count_documents(filter_dict)

        # 如果存在最近通知，则不允许发送
        return recent_count == 0

    async def create_notification_with_check(
        self,
        notification_data: NotificationCreate,
        user_id: Optional[str] = None,
        check_position: bool = True,
        check_frequency: bool = True,
        frequency_threshold: int = 30
    ) -> Optional[str]:
        """
        创建通知（带持仓关联和频率检查）

        Args:
            notification_data: 通知数据
            user_id: 用户ID
            check_position: 是否检查持仓关联
            check_frequency: 是否检查频率
            frequency_threshold: 频率阈值（分钟）

        Returns:
            通知ID（如果创建成功）或 None（如果被过滤）
        """
        # 持仓关联检查
        if check_position and notification_data.target_symbol:
            is_monitored = await self.check_symbol_monitored(
                notification_data.target_symbol,
                user_id
            )
            if not is_monitored:
                logger.debug(
                    f"股票 {notification_data.target_symbol} 不在监控列表，跳过通知创建"
                )
                return None

        # 频率检查
        if check_frequency:
            can_send = await self.check_notification_frequency(
                notification_data.type,
                notification_data.target_symbol,
                user_id,
                frequency_threshold
            )
            if not can_send:
                logger.debug(
                    f"通知频率过高，跳过创建: 类型={notification_data.type}, "
                    f"股票={notification_data.target_symbol}"
                )
                return None

        # 创建通知
        return await self.create_notification(notification_data, user_id)

    async def create_notification(
        self,
        notification_data: NotificationCreate,
        user_id: Optional[str] = None
    ) -> str:
        """
        创建通知

        Args:
            notification_data: 通知数据
            user_id: 用户ID（可选）

        Returns:
            通知ID
        """
        notification_id = str(uuid.uuid4())

        notification = NotificationModel(
            notification_id=notification_id,
            user_id=user_id,
            type=notification_data.type,
            priority=notification_data.priority,
            title=notification_data.title,
            content=notification_data.content,
            target_symbol=notification_data.target_symbol,
            strategy_id=notification_data.strategy_id,
            task_id=notification_data.task_id,
            trigger_condition=notification_data.trigger_condition,
            trigger_value=notification_data.trigger_value,
            extra_data=notification_data.extra_data,
            follow_up=notification_data.follow_up,
            follow_up_time=notification_data.follow_up_time,
        )

        await self.collection.insert_one(notification.dict())

        logger.info(
            f"创建通知: {notification_id}, 类型: {notification_data.type}, "
            f"优先级: {notification_data.priority}, 标题: {notification_data.title}"
        )

        return notification_id

    async def get_notification(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个通知

        Args:
            notification_id: 通知ID

        Returns:
            通知数据
        """
        notification = await self.collection.find_one({"notification_id": notification_id})
        return notification

    async def query_notifications(
        self,
        query: NotificationQuery,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询通知列表

        Args:
            query: 查询条件
            user_id: 用户ID（可选）

        Returns:
            通知列表和统计信息
        """
        # 构建查询条件
        filter_dict = {}
        if user_id:
            filter_dict["user_id"] = user_id

        if query.type:
            filter_dict["type"] = query.type
        if query.priority:
            filter_dict["priority"] = query.priority
        if query.read_status is not None:
            filter_dict["read_status"] = query.read_status
        if query.target_symbol:
            filter_dict["target_symbol"] = query.target_symbol
        if query.strategy_id:
            filter_dict["strategy_id"] = query.strategy_id
        if query.follow_up is not None:
            filter_dict["follow_up"] = query.follow_up

        # 时间范围
        if query.start_date or query.end_date:
            filter_dict["created_at"] = {}
            if query.start_date:
                filter_dict["created_at"]["$gte"] = query.start_date
            if query.end_date:
                filter_dict["created_at"]["$lte"] = query.end_date

        # 查询总数
        total = await self.collection.count_documents(filter_dict)

        # 查询未读数量
        unread_filter = filter_dict.copy()
        unread_filter["read_status"] = False
        unread_count = await self.collection.count_documents(unread_filter)

        # 查询通知列表（按创建时间倒序）
        cursor = self.collection.find(filter_dict).sort("created_at", -1).skip(query.offset).limit(query.limit)
        notifications = await cursor.to_list(length=query.limit)

        return {
            "total": total,
            "unread_count": unread_count,
            "notifications": notifications,
        }

    async def update_notification(
        self,
        notification_id: str,
        update_data: NotificationUpdate
    ) -> bool:
        """
        更新通知

        Args:
            notification_id: 通知ID
            update_data: 更新数据

        Returns:
            是否更新成功
        """
        update_dict = {}
        if update_data.read_status is not None:
            update_dict["read_status"] = update_data.read_status
            if update_data.read_status:
                update_dict["read_at"] = datetime.now()

        if update_data.follow_up is not None:
            update_dict["follow_up"] = update_data.follow_up
        if update_data.follow_up_time is not None:
            update_dict["follow_up_time"] = update_data.follow_up_time

        update_dict["updated_at"] = datetime.now()

        result = await self.collection.update_one(
            {"notification_id": notification_id},
            {"$set": update_dict}
        )

        return result.modified_count > 0

    async def mark_as_read(self, notification_id: str) -> bool:
        """
        标记为已读

        Args:
            notification_id: 通知ID

        Returns:
            是否标记成功
        """
        result = await self.collection.update_one(
            {"notification_id": notification_id},
            {
                "$set": {
                    "read_status": True,
                    "read_at": datetime.now(),
                    "updated_at": datetime.now(),
                }
            }
        )
        return result.modified_count > 0

    async def mark_all_as_read(self, user_id: Optional[str] = None) -> int:
        """
        标记所有通知为已读

        Args:
            user_id: 用户ID（可选）

        Returns:
            标记数量
        """
        filter_dict = {"read_status": False}
        if user_id:
            filter_dict["user_id"] = user_id

        result = await self.collection.update_many(
            filter_dict,
            {
                "$set": {
                    "read_status": True,
                    "read_at": datetime.now(),
                    "updated_at": datetime.now(),
                }
            }
        )
        return result.modified_count

    async def delete_notification(self, notification_id: str) -> bool:
        """
        删除通知

        Args:
            notification_id: 通知ID

        Returns:
            是否删除成功
        """
        result = await self.collection.delete_one({"notification_id": notification_id})
        return result.deleted_count > 0

    async def mark_as_pushed(
        self,
        notification_id: str,
        push_channel: str
    ) -> bool:
        """
        标记为已推送

        Args:
            notification_id: 通知ID
            push_channel: 推送渠道

        Returns:
            是否标记成功
        """
        result = await self.collection.update_one(
            {"notification_id": notification_id},
            {
                "$set": {
                    "pushed": True,
                    "push_channel": push_channel,
                    "pushed_at": datetime.now(),
                    "updated_at": datetime.now(),
                }
            }
        )
        return result.modified_count > 0

    async def generate_structured_message(
        self,
        notification_type: NotificationType,
        **kwargs
    ) -> Dict[str, str]:
        """
        生成结构化消息内容

        Args:
            notification_type: 通知类型
            **kwargs: 消息参数

        Returns:
            包含 title 和 content 的字典
        """
        if notification_type == NotificationType.RISK_ALERT:
            # 风控预警
            symbol = kwargs.get('symbol', '未知')
            condition = kwargs.get('condition', '未知条件')
            value = kwargs.get('value', 0)
            threshold = kwargs.get('threshold', 0)

            title = f"【风控预警】{symbol} 触发{condition}"
            content = (
                f"标的：{symbol}\n"
                f"触发条件：{condition}\n"
                f"当前值：{value}\n"
                f"阈值：{threshold}\n"
                f"操作指引：请及时检查持仓，必要时调整仓位或止损"
            )

        elif notification_type == NotificationType.STRATEGY_SIGNAL:
            # 策略信号
            symbol = kwargs.get('symbol', '未知')
            signal = kwargs.get('signal', '未知')
            strategy_name = kwargs.get('strategy_name', '策略')
            price = kwargs.get('price', 0)

            title = f"【策略信号】{symbol} - {signal}"
            content = (
                f"标的：{symbol}\n"
                f"策略：{strategy_name}\n"
                f"信号：{signal}\n"
                f"当前价格：{price:.2f}\n"
                f"操作指引：根据策略逻辑执行相应操作"
            )

        elif notification_type == NotificationType.BACKTEST_COMPLETE:
            # 回测完成
            symbol = kwargs.get('symbol', '未知')
            strategy_type = kwargs.get('strategy_type', '未知策略')
            total_return = kwargs.get('total_return', 0)
            sharpe_ratio = kwargs.get('sharpe_ratio', 0)

            title = f"【回测完成】{symbol} - {strategy_type}"
            content = (
                f"标的：{symbol}\n"
                f"策略：{strategy_type}\n"
                f"总收益率：{total_return*100:.2f}%\n"
                f"夏普比率：{sharpe_ratio:.2f}\n"
                f"操作指引：查看详细回测报告"
            )

        elif notification_type == NotificationType.DATA_ANOMALY:
            # 数据异常
            source = kwargs.get('source', '未知数据源')
            error_msg = kwargs.get('error_msg', '数据异常')

            title = f"【数据异常】{source}"
            content = (
                f"数据源：{source}\n"
                f"异常描述：{error_msg}\n"
                f"操作指引：检查数据源连接或稍后重试"
            )

        else:
            # 默认格式
            title = kwargs.get('title', '系统通知')
            content = kwargs.get('content', '')

        return {
            "title": title,
            "content": content
        }

    async def create_anomaly_alert(
        self,
        anomaly_type: str,
        **kwargs
    ) -> Optional[str]:
        """
        创建异常预警通知

        Args:
            anomaly_type: 异常类型 (max_drawdown/data_source/suspended/price_limit)
            **kwargs: 异常参数

        Returns:
            通知ID
        """
        if anomaly_type == "max_drawdown":
            # 最大回撤预警
            symbol = kwargs.get('symbol', '未知')
            current_drawdown = kwargs.get('current_drawdown', 0)
            threshold = kwargs.get('threshold', 0.2)

            notification_data = NotificationCreate(
                type=NotificationType.RISK_ALERT,
                priority=NotificationPriority.URGENT,
                title=f"【回撤预警】{symbol} 触发最大回撤阈值",
                content=(
                    f"标的：{symbol}\n"
                    f"当前回撤：{current_drawdown*100:.2f}%\n"
                    f"预警阈值：{threshold*100:.2f}%\n"
                    f"操作指引：建议立即检查持仓，考虑减仓或止损"
                ),
                target_symbol=symbol,
                trigger_condition=f"最大回撤 >= {threshold*100:.2f}%",
                trigger_value=current_drawdown,
                extra_data={"anomaly_type": "max_drawdown"},
            )

        elif anomaly_type == "data_source":
            # 数据源中断
            source = kwargs.get('source', '未知数据源')
            error_msg = kwargs.get('error_msg', '数据源连接失败')
            retry_count = kwargs.get('retry_count', 0)

            notification_data = NotificationCreate(
                type=NotificationType.DATA_ANOMALY,
                priority=NotificationPriority.URGENT,
                title=f"【数据异常】{source} 数据源中断",
                content=(
                    f"数据源：{source}\n"
                    f"异常描述：{error_msg}\n"
                    f"重试次数：{retry_count}\n"
                    f"操作指引：检查网络连接和数据源状态"
                ),
                trigger_condition="数据源连接失败",
                extra_data={
                    "anomaly_type": "data_source",
                    "source": source,
                    "retry_count": retry_count
                },
            )

        elif anomaly_type == "suspended":
            # 停牌预警
            symbol = kwargs.get('symbol', '未知')
            suspend_reason = kwargs.get('reason', '未知原因')

            notification_data = NotificationCreate(
                type=NotificationType.POSITION_REMINDER,
                priority=NotificationPriority.URGENT,
                title=f"【停牌预警】{symbol} 已停牌",
                content=(
                    f"标的：{symbol}\n"
                    f"停牌原因：{suspend_reason}\n"
                    f"操作指引：关注复牌公告，评估持仓风险"
                ),
                target_symbol=symbol,
                trigger_condition="股票停牌",
                extra_data={"anomaly_type": "suspended"},
            )

        elif anomaly_type == "price_limit":
            # 涨跌停预警
            symbol = kwargs.get('symbol', '未知')
            limit_type = kwargs.get('limit_type', 'up')  # up/down
            price = kwargs.get('price', 0)

            limit_text = "涨停" if limit_type == "up" else "跌停"
            priority = NotificationPriority.URGENT if limit_type == "down" else NotificationPriority.NORMAL

            notification_data = NotificationCreate(
                type=NotificationType.POSITION_REMINDER,
                priority=priority,
                title=f"【价格预警】{symbol} {limit_text}",
                content=(
                    f"标的：{symbol}\n"
                    f"状态：{limit_text}\n"
                    f"价格：{price:.2f}\n"
                    f"操作指引：{'关注是否需要止损' if limit_type == 'down' else '关注盈利时机'}"
                ),
                target_symbol=symbol,
                trigger_condition=limit_text,
                trigger_value=price,
                extra_data={"anomaly_type": "price_limit", "limit_type": limit_type},
            )

        else:
            logger.warning(f"未知的异常类型: {anomaly_type}")
            return None

        # 使用带检查的创建方法
        return await self.create_notification_with_check(
            notification_data,
            check_position=True,
            check_frequency=True,
            frequency_threshold=60  # 异常预警1小时内不重复
        )


# 全局通知服务实例（需要在应用启动时初始化）
_notification_service: Optional[NotificationService] = None


def get_notification_service(db: AsyncIOMotorDatabase) -> NotificationService:
    """获取通知服务实例"""
    return NotificationService(db)
