"""
策略对话服务
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId
import logging

from app.core.database import get_mongodb
from app.models.strategy import (
    StrategyConversationModel,
    ConversationMessageModel,
    ConversationStatus,
    MessageRole,
)

logger = logging.getLogger(__name__)


class ConversationService:
    """策略对话服务"""

    def __init__(self):
        self.db = get_mongodb()
        self.conversations_collection = "strategy_conversations"
        self.messages_collection = "conversation_messages"

    async def create_conversation(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        创建新的策略对话

        Args:
            user_id: 用户ID
            title: 对话标题
            description: 对话描述
            tags: 对话标签

        Returns:
            对话ID
        """
        conversation = StrategyConversationModel(
            user_id=user_id,
            title=title,
            description=description,
            tags=tags or [],
            status=ConversationStatus.ACTIVE,
        )

        result = await self.db[self.conversations_collection].insert_one(
            conversation.dict()
        )
        conversation_id = str(result.inserted_id)

        logger.info(f"创建对话成功: {conversation_id}")
        return conversation_id

    async def get_conversation(
        self, conversation_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取对话详情

        Args:
            conversation_id: 对话ID
            user_id: 用户ID（用于权限校验）

        Returns:
            对话详情字典
        """
        query = {"_id": ObjectId(conversation_id)}
        if user_id:
            query["user_id"] = user_id

        conversation = await self.db[self.conversations_collection].find_one(query)

        if conversation:
            conversation["id"] = str(conversation.pop("_id"))
            return conversation

        return None

    async def list_conversations(
        self,
        user_id: str,
        status: Optional[ConversationStatus] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取用户的对话列表

        Args:
            user_id: 用户ID
            status: 对话状态筛选
            skip: 跳过数量
            limit: 限制数量

        Returns:
            对话列表
        """
        query = {"user_id": user_id}
        if status:
            query["status"] = status

        cursor = (
            self.db[self.conversations_collection]
            .find(query)
            .sort("updated_at", -1)
            .skip(skip)
            .limit(limit)
        )

        conversations = []
        async for conversation in cursor:
            conversation["id"] = str(conversation.pop("_id"))
            conversations.append(conversation)

        return conversations

    async def update_conversation(
        self, conversation_id: str, user_id: str, **updates
    ) -> bool:
        """
        更新对话信息

        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            **updates: 更新字段

        Returns:
            是否成功
        """
        updates["updated_at"] = datetime.now()

        result = await self.db[self.conversations_collection].update_one(
            {"_id": ObjectId(conversation_id), "user_id": user_id}, {"$set": updates}
        )

        return result.modified_count > 0

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """
        删除对话（软删除，标记为归档）

        Args:
            conversation_id: 对话ID
            user_id: 用户ID

        Returns:
            是否成功
        """
        return await self.update_conversation(
            conversation_id, user_id, status=ConversationStatus.ARCHIVED
        )

    async def add_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        generated_code: Optional[str] = None,
        strategy_version_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        添加对话消息

        Args:
            conversation_id: 对话ID
            role: 消息角色
            content: 消息内容
            generated_code: 生成的代码
            strategy_version_id: 关联的策略版本ID
            metadata: 元数据

        Returns:
            消息ID
        """
        message = ConversationMessageModel(
            conversation_id=conversation_id,
            role=role,
            content=content,
            generated_code=generated_code,
            strategy_version_id=strategy_version_id,
            metadata=metadata or {},
        )

        result = await self.db[self.messages_collection].insert_one(message.dict())
        message_id = str(result.inserted_id)

        # 更新对话的消息计数和最后消息时间
        await self.db[self.conversations_collection].update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$inc": {"message_count": 1},
                "$set": {
                    "last_message_at": datetime.now(),
                    "updated_at": datetime.now(),
                },
            },
        )

        logger.info(f"添加消息成功: {message_id}")
        return message_id

    async def get_messages(
        self,
        conversation_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        获取对话消息列表

        Args:
            conversation_id: 对话ID
            skip: 跳过数量
            limit: 限制数量

        Returns:
            消息列表
        """
        cursor = (
            self.db[self.messages_collection]
            .find({"conversation_id": conversation_id})
            .sort("created_at", 1)
            .skip(skip)
            .limit(limit)
        )

        messages = []
        async for message in cursor:
            message["id"] = str(message.pop("_id"))
            messages.append(message)

        return messages

    async def get_conversation_context(
        self, conversation_id: str, max_messages: int = 10
    ) -> str:
        """
        获取对话上下文（用于AI生成）

        Args:
            conversation_id: 对话ID
            max_messages: 最大消息数

        Returns:
            格式化的对话上下文字符串
        """
        messages = await self.get_messages(
            conversation_id, skip=0, limit=max_messages
        )

        context_parts = []
        for msg in messages:
            role_label = "用户" if msg["role"] == MessageRole.USER else "助手"
            context_parts.append(f"{role_label}: {msg['content']}")

            if msg.get("generated_code"):
                context_parts.append(f"```python\n{msg['generated_code']}\n```")

        return "\n\n".join(context_parts)


# 全局服务实例
conversation_service = ConversationService()
