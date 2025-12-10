"""
市场数据缓存服务
使用 Redis 缓存实时行情数据，TTL=10秒
"""
import json
from typing import Optional, Any, Dict
from datetime import timedelta
import logging

from app.core.database import get_redis

logger = logging.getLogger(__name__)


class MarketDataCacheService:
    """市场数据缓存服务"""

    def __init__(self, ttl_seconds: int = 10):
        """
        初始化缓存服务

        Args:
            ttl_seconds: 缓存过期时间（秒），默认10秒
        """
        self.ttl = ttl_seconds
        self.prefix = "market_data"

    def _get_key(self, data_type: str, identifier: str) -> str:
        """生成缓存键"""
        return f"{self.prefix}:{data_type}:{identifier}"

    async def get_cached_data(
        self,
        data_type: str,
        identifier: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存数据

        Args:
            data_type: 数据类型（如 realtime_quote, kline 等）
            identifier: 数据标识符（如股票代码）

        Returns:
            缓存的数据字典，如果不存在则返回 None
        """
        try:
            redis = get_redis()
            key = self._get_key(data_type, identifier)

            cached_value = await redis.get(key)
            if cached_value:
                logger.debug(f"缓存命中: {key}")
                return json.loads(cached_value)

            logger.debug(f"缓存未命中: {key}")
            return None

        except Exception as e:
            logger.error(f"获取缓存失败: {str(e)}")
            return None

    async def set_cached_data(
        self,
        data_type: str,
        identifier: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存数据

        Args:
            data_type: 数据类型
            identifier: 数据标识符
            data: 要缓存的数据
            ttl: 过期时间（秒），如果为 None 则使用默认值

        Returns:
            是否成功
        """
        try:
            redis = get_redis()
            key = self._get_key(data_type, identifier)
            ttl = ttl or self.ttl

            await redis.setex(
                key,
                timedelta(seconds=ttl),
                json.dumps(data, ensure_ascii=False)
            )

            logger.debug(f"缓存已设置: {key}, TTL={ttl}秒")
            return True

        except Exception as e:
            logger.error(f"设置缓存失败: {str(e)}")
            return False

    async def delete_cached_data(
        self,
        data_type: str,
        identifier: str
    ) -> bool:
        """
        删除缓存数据

        Args:
            data_type: 数据类型
            identifier: 数据标识符

        Returns:
            是否成功
        """
        try:
            redis = get_redis()
            key = self._get_key(data_type, identifier)

            await redis.delete(key)
            logger.debug(f"缓存已删除: {key}")
            return True

        except Exception as e:
            logger.error(f"删除缓存失败: {str(e)}")
            return False

    async def clear_all_cache(self, data_type: Optional[str] = None) -> bool:
        """
        清除所有缓存或指定类型的缓存

        Args:
            data_type: 数据类型，如果为 None 则清除所有市场数据缓存

        Returns:
            是否成功
        """
        try:
            redis = get_redis()

            if data_type:
                pattern = f"{self.prefix}:{data_type}:*"
            else:
                pattern = f"{self.prefix}:*"

            # 查找所有匹配的键
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await redis.delete(*keys)
                logger.info(f"已清除 {len(keys)} 个缓存项")

            return True

        except Exception as e:
            logger.error(f"清除缓存失败: {str(e)}")
            return False


# 全局缓存服务实例
cache_service = MarketDataCacheService()
