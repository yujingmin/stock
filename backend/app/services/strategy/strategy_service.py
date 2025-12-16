"""
策略管理服务
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
import logging

from app.core.database import get_mongodb
from app.models.strategy import StrategyVersionModel, StrategyStatus

logger = logging.getLogger(__name__)


class StrategyService:
    """策略管理服务"""

    def __init__(self):
        self.db = get_mongodb()
        self.strategies_collection = "strategy_versions"

    async def create_strategy_version(
        self,
        strategy_name: str,
        user_id: str,
        code: str,
        conversation_id: Optional[str] = None,
        message_id: Optional[str] = None,
        strategy_type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        version_description: Optional[str] = None,
    ) -> str:
        """
        创建策略版本

        Args:
            strategy_name: 策略名称
            user_id: 用户ID
            code: 策略代码
            conversation_id: 关联的对话ID
            message_id: 生成此版本的消息ID
            strategy_type: 策略类型
            parameters: 策略参数
            version_description: 版本说明

        Returns:
            策略版本ID
        """
        # 获取当前策略的最新版本号
        latest_version = await self.db[self.strategies_collection].find_one(
            {"strategy_name": strategy_name, "user_id": user_id},
            sort=[("version", -1)],
        )

        version = 1 if not latest_version else latest_version["version"] + 1

        strategy = StrategyVersionModel(
            strategy_name=strategy_name,
            user_id=user_id,
            code=code,
            conversation_id=conversation_id,
            message_id=message_id,
            version=version,
            version_description=version_description,
            strategy_type=strategy_type,
            parameters=parameters or {},
            status=StrategyStatus.DRAFT,
        )

        result = await self.db[self.strategies_collection].insert_one(strategy.dict())
        strategy_id = str(result.inserted_id)

        # 更新对话的策略关联
        if conversation_id:
            from app.services.strategy.conversation_service import conversation_service

            await conversation_service.update_conversation(
                conversation_id, user_id, current_strategy_id=strategy_id
            )
            await self.db["strategy_conversations"].update_one(
                {"_id": ObjectId(conversation_id)}, {"$inc": {"version_count": 1}}
            )

        logger.info(f"创建策略版本成功: {strategy_id}")
        return strategy_id

    async def get_strategy_version(
        self, strategy_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取策略版本详情

        Args:
            strategy_id: 策略ID
            user_id: 用户ID（用于权限校验）

        Returns:
            策略详情字典
        """
        query = {"_id": ObjectId(strategy_id)}
        if user_id:
            query["user_id"] = user_id

        strategy = await self.db[self.strategies_collection].find_one(query)

        if strategy:
            strategy["id"] = str(strategy.pop("_id"))
            return strategy

        return None

    async def list_strategy_versions(
        self,
        user_id: str,
        strategy_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取策略版本列表

        Args:
            user_id: 用户ID
            strategy_name: 策略名称筛选
            skip: 跳过数量
            limit: 限制数量

        Returns:
            策略版本列表
        """
        query = {"user_id": user_id}
        if strategy_name:
            query["strategy_name"] = strategy_name

        cursor = (
            self.db[self.strategies_collection]
            .find(query)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

        strategies = []
        async for strategy in cursor:
            strategy["id"] = str(strategy.pop("_id"))
            strategies.append(strategy)

        return strategies

    async def update_strategy_version(
        self, strategy_id: str, user_id: str, **updates
    ) -> bool:
        """
        更新策略版本

        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            **updates: 更新字段

        Returns:
            是否成功
        """
        result = await self.db[self.strategies_collection].update_one(
            {"_id": ObjectId(strategy_id), "user_id": user_id}, {"$set": updates}
        )

        return result.modified_count > 0

    async def link_backtest_result(
        self, strategy_id: str, user_id: str, backtest_result_id: str, metrics: Dict[str, Any]
    ) -> bool:
        """
        关联回测结果

        Args:
            strategy_id: 策略ID
            user_id: 用户ID
            backtest_result_id: 回测结果ID
            metrics: 绩效指标

        Returns:
            是否成功
        """
        return await self.update_strategy_version(
            strategy_id,
            user_id,
            backtest_result_id=backtest_result_id,
            performance_metrics=metrics,
        )

    async def compare_versions(
        self, strategy_id_1: str, strategy_id_2: str, user_id: str
    ) -> Dict[str, Any]:
        """
        比较两个策略版本

        Args:
            strategy_id_1: 策略版本1 ID
            strategy_id_2: 策略版本2 ID
            user_id: 用户ID

        Returns:
            版本对比结果
        """
        strategy1 = await self.get_strategy_version(strategy_id_1, user_id)
        strategy2 = await self.get_strategy_version(strategy_id_2, user_id)

        if not strategy1 or not strategy2:
            raise ValueError("策略版本不存在")

        # 简单的差异比较
        return {
            "version_1": {
                "id": strategy1["id"],
                "version": strategy1["version"],
                "code_length": len(strategy1["code"]),
                "parameters": strategy1["parameters"],
                "created_at": strategy1["created_at"],
            },
            "version_2": {
                "id": strategy2["id"],
                "version": strategy2["version"],
                "code_length": len(strategy2["code"]),
                "parameters": strategy2["parameters"],
                "created_at": strategy2["created_at"],
            },
            "code_diff": {
                "added_lines": 0,  # 可以使用 difflib 计算
                "removed_lines": 0,
            },
        }


# 全局服务实例
strategy_service = StrategyService()
