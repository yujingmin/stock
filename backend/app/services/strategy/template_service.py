"""
策略模板服务
"""
from typing import Optional, List, Dict, Any
from bson import ObjectId
import logging

from app.core.database import get_mongodb
from app.models.strategy import StrategyTemplateModel

logger = logging.getLogger(__name__)


class TemplateService:
    """策略模板服务"""

    def __init__(self):
        self.db = get_mongodb()
        self.templates_collection = "strategy_templates"

    async def create_template(
        self,
        name: str,
        description: str,
        code: str,
        strategy_type: str,
        difficulty: str = "intermediate",
        risk_level: str = "medium",
        suitable_markets: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        parameters: Optional[Dict[str, Any]] = None,
        created_by: str = "system",
        is_public: bool = True,
    ) -> str:
        """
        创建策略模板

        Args:
            name: 模板名称
            description: 模板描述
            code: 模板代码
            strategy_type: 策略类型
            difficulty: 难度级别
            risk_level: 风险等级
            suitable_markets: 适用市场
            tags: 标签
            parameters: 参数说明
            created_by: 创建者
            is_public: 是否公开

        Returns:
            模板ID
        """
        template = StrategyTemplateModel(
            name=name,
            description=description,
            code=code,
            strategy_type=strategy_type,
            difficulty=difficulty,
            risk_level=risk_level,
            suitable_markets=suitable_markets or [],
            tags=tags or [],
            parameters=parameters or {},
            created_by=created_by,
            is_public=is_public,
        )

        result = await self.db[self.templates_collection].insert_one(template.dict())
        template_id = str(result.inserted_id)

        logger.info(f"创建模板成功: {template_id}")
        return template_id

    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        获取模板详情

        Args:
            template_id: 模板ID

        Returns:
            模板详情字典
        """
        template = await self.db[self.templates_collection].find_one(
            {"_id": ObjectId(template_id)}
        )

        if template:
            template["id"] = str(template.pop("_id"))
            return template

        return None

    async def list_templates(
        self,
        strategy_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取模板列表

        Args:
            strategy_type: 策略类型筛选
            difficulty: 难度筛选
            tags: 标签筛选
            skip: 跳过数量
            limit: 限制数量

        Returns:
            模板列表
        """
        query = {"is_public": True}
        if strategy_type:
            query["strategy_type"] = strategy_type
        if difficulty:
            query["difficulty"] = difficulty
        if tags:
            query["tags"] = {"$in": tags}

        cursor = (
            self.db[self.templates_collection]
            .find(query)
            .sort("usage_count", -1)
            .skip(skip)
            .limit(limit)
        )

        templates = []
        async for template in cursor:
            template["id"] = str(template.pop("_id"))
            templates.append(template)

        return templates

    async def increment_usage(self, template_id: str) -> bool:
        """
        增加模板使用次数

        Args:
            template_id: 模板ID

        Returns:
            是否成功
        """
        result = await self.db[self.templates_collection].update_one(
            {"_id": ObjectId(template_id)}, {"$inc": {"usage_count": 1}}
        )

        return result.modified_count > 0

    async def search_templates(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索模板

        Args:
            keyword: 关键词

        Returns:
            模板列表
        """
        query = {
            "$or": [
                {"name": {"$regex": keyword, "$options": "i"}},
                {"description": {"$regex": keyword, "$options": "i"}},
                {"tags": {"$regex": keyword, "$options": "i"}},
            ],
            "is_public": True,
        }

        cursor = self.db[self.templates_collection].find(query).sort("usage_count", -1)

        templates = []
        async for template in cursor:
            template["id"] = str(template.pop("_id"))
            templates.append(template)

        return templates


# 全局服务实例
template_service = TemplateService()
