"""
股票筛选服务
支持按条件筛选股票，保存和复用筛选规则
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.services.market_data.akshare_client import akshare_client
from app.core.database import get_mongodb

logger = logging.getLogger(__name__)


class ScreenService:
    """股票筛选服务"""

    def __init__(self):
        self.collection_name = "screen_rules"

    async def screen_stocks(
        self,
        conditions: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        根据条件筛选股票

        Args:
            conditions: 筛选条件字典
                {
                    "min_pe": 最小市盈率,
                    "max_pe": 最大市盈率,
                    "min_pb": 最小市净率,
                    "max_pb": 最大市净率,
                    "min_dividend_yield": 最小股息率,
                    "min_market_cap": 最小市值（亿元）,
                    "max_market_cap": 最大市值（亿元）
                }

        Returns:
            符合条件的股票列表
        """
        try:
            # 获取所有股票列表
            all_stocks = await akshare_client.get_stock_list()

            result = []
            for stock in all_stocks[:100]:  # 限制数量以提高性能（实际应分批处理）
                try:
                    # 获取股票指标
                    indicators = await akshare_client.get_stock_indicators(stock["symbol"])

                    # 应用筛选条件
                    if self._match_conditions(indicators, conditions):
                        result.append({
                            "symbol": stock["symbol"],
                            "name": stock["name"],
                            "pe_ratio": indicators.get("pe_ratio"),
                            "pb_ratio": indicators.get("pb_ratio"),
                            "dividend_yield": indicators.get("dividend_yield"),
                            "market_cap": indicators.get("total_market_cap"),
                        })
                except Exception as e:
                    logger.warning(f"获取股票 {stock['symbol']} 指标失败: {str(e)}")
                    continue

            logger.info(f"筛选完成，找到 {len(result)} 只符合条件的股票")
            return result

        except Exception as e:
            logger.error(f"股票筛选失败: {str(e)}")
            raise

    def _match_conditions(
        self,
        indicators: Dict[str, Any],
        conditions: Dict[str, Any]
    ) -> bool:
        """
        检查股票指标是否符合筛选条件

        Args:
            indicators: 股票指标
            conditions: 筛选条件

        Returns:
            是否符合条件
        """
        # 市盈率筛选
        if "min_pe" in conditions:
            pe = indicators.get("pe_ratio")
            if pe is None or float(pe) < conditions["min_pe"]:
                return False

        if "max_pe" in conditions:
            pe = indicators.get("pe_ratio")
            if pe is None or float(pe) > conditions["max_pe"]:
                return False

        # 市净率筛选
        if "min_pb" in conditions:
            pb = indicators.get("pb_ratio")
            if pb is None or float(pb) < conditions["min_pb"]:
                return False

        if "max_pb" in conditions:
            pb = indicators.get("pb_ratio")
            if pb is None or float(pb) > conditions["max_pb"]:
                return False

        # 股息率筛选
        if "min_dividend_yield" in conditions:
            dy = indicators.get("dividend_yield")
            if dy is None or float(dy) < conditions["min_dividend_yield"]:
                return False

        # 市值筛选（单位：亿元）
        if "min_market_cap" in conditions:
            mc = indicators.get("total_market_cap")
            if mc is None:
                return False
            # 转换为亿元
            mc_yi = float(mc) / 100000000
            if mc_yi < conditions["min_market_cap"]:
                return False

        if "max_market_cap" in conditions:
            mc = indicators.get("total_market_cap")
            if mc is None:
                return False
            mc_yi = float(mc) / 100000000
            if mc_yi > conditions["max_market_cap"]:
                return False

        return True

    async def save_screen_rule(
        self,
        name: str,
        conditions: Dict[str, Any],
        description: Optional[str] = None
    ) -> str:
        """
        保存筛选规则

        Args:
            name: 规则名称
            conditions: 筛选条件
            description: 规则描述

        Returns:
            规则ID
        """
        try:
            db = get_mongodb()
            collection = db[self.collection_name]

            rule = {
                "name": name,
                "description": description,
                "conditions": conditions,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            result = await collection.insert_one(rule)
            rule_id = str(result.inserted_id)

            logger.info(f"筛选规则已保存: {name} (ID: {rule_id})")
            return rule_id

        except Exception as e:
            logger.error(f"保存筛选规则失败: {str(e)}")
            raise

    async def get_screen_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        获取筛选规则

        Args:
            rule_id: 规则ID

        Returns:
            规则字典
        """
        try:
            from bson import ObjectId

            db = get_mongodb()
            collection = db[self.collection_name]

            rule = await collection.find_one({"_id": ObjectId(rule_id)})

            if rule:
                rule["_id"] = str(rule["_id"])
                return rule

            return None

        except Exception as e:
            logger.error(f"获取筛选规则失败: {str(e)}")
            raise

    async def list_screen_rules(self) -> List[Dict[str, Any]]:
        """
        列出所有筛选规则

        Returns:
            规则列表
        """
        try:
            db = get_mongodb()
            collection = db[self.collection_name]

            cursor = collection.find().sort("created_at", -1)
            rules = []

            async for rule in cursor:
                rule["_id"] = str(rule["_id"])
                rules.append(rule)

            return rules

        except Exception as e:
            logger.error(f"列出筛选规则失败: {str(e)}")
            raise

    async def delete_screen_rule(self, rule_id: str) -> bool:
        """
        删除筛选规则

        Args:
            rule_id: 规则ID

        Returns:
            是否成功
        """
        try:
            from bson import ObjectId

            db = get_mongodb()
            collection = db[self.collection_name]

            result = await collection.delete_one({"_id": ObjectId(rule_id)})

            if result.deleted_count > 0:
                logger.info(f"筛选规则已删除: {rule_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"删除筛选规则失败: {str(e)}")
            raise

    async def update_screen_rule(
        self,
        rule_id: str,
        name: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        更新筛选规则

        Args:
            rule_id: 规则ID
            name: 新名称
            conditions: 新筛选条件
            description: 新描述

        Returns:
            是否成功
        """
        try:
            from bson import ObjectId

            db = get_mongodb()
            collection = db[self.collection_name]

            update_data = {"updated_at": datetime.now()}

            if name is not None:
                update_data["name"] = name
            if conditions is not None:
                update_data["conditions"] = conditions
            if description is not None:
                update_data["description"] = description

            result = await collection.update_one(
                {"_id": ObjectId(rule_id)},
                {"$set": update_data}
            )

            if result.modified_count > 0:
                logger.info(f"筛选规则已更新: {rule_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"更新筛选规则失败: {str(e)}")
            raise


# 全局服务实例
screen_service = ScreenService()
