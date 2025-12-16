"""
AI 对话服务 - 集成 AI 生成和对话管理
"""
from typing import Optional, Dict, Any
import logging

from app.services.ai.strategy_generator import StrategyGenerator
from app.services.strategy.conversation_service import conversation_service
from app.services.strategy.strategy_service import strategy_service
from app.models.strategy import MessageRole

logger = logging.getLogger(__name__)


class AIConversationService:
    """AI 对话服务 - 处理用户消息并生成策略代码"""

    def __init__(self):
        """初始化服务"""
        self.strategy_generator = StrategyGenerator()
        self.conversation_service = conversation_service
        self.strategy_service = strategy_service

    async def process_user_message(
        self,
        conversation_id: str,
        user_id: str,
        user_message: str,
        auto_generate_code: bool = True,
        strategy_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理用户消息并生成响应

        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            user_message: 用户消息
            auto_generate_code: 是否自动生成代码
            strategy_type: 策略类型提示

        Returns:
            {
                "user_message_id": "用户消息ID",
                "assistant_message_id": "助手消息ID",
                "assistant_response": "助手回复文本",
                "generated_code": "生成的代码（如果有）",
                "strategy_version_id": "策略版本ID（如果生成了代码）"
            }
        """
        # 1. 保存用户消息
        user_message_id = await self.conversation_service.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=user_message,
        )

        logger.info(f"收到用户消息: {user_message_id}")

        # 2. 获取对话历史
        messages = await self.conversation_service.get_messages(
            conversation_id, limit=10
        )

        conversation_history = [
            {"role": msg["role"], "content": msg["content"]} for msg in messages[:-1]
        ]  # 不包括刚添加的用户消息

        # 3. 判断是否需要生成代码
        should_generate = auto_generate_code and self._should_generate_code(
            user_message
        )

        generated_code = None
        strategy_version_id = None
        assistant_response = ""

        if should_generate:
            try:
                # 4. 调用 AI 生成策略代码
                logger.info("开始生成策略代码...")
                generation_result = self.strategy_generator.generate_strategy(
                    user_requirement=user_message,
                    conversation_history=conversation_history,
                    strategy_type=strategy_type,
                    use_template=True,
                )

                generated_code = generation_result["code"]
                strategy_name = generation_result["strategy_name"]
                description = generation_result["description"]
                parameters = generation_result["parameters"]

                logger.info(f"策略代码生成成功: {strategy_name}")

                # 5. 保存策略版本
                strategy_version_id = await self.strategy_service.create_strategy_version(
                    strategy_name=strategy_name,
                    user_id=user_id,
                    code=generated_code,
                    conversation_id=conversation_id,
                    message_id=None,  # 将在后面更新
                    strategy_type=strategy_type or "custom",
                    parameters=parameters,
                    version_description=description,
                )

                logger.info(f"策略版本保存成功: {strategy_version_id}")

                # 6. 生成助手回复
                assistant_response = self._format_assistant_response(
                    strategy_name=strategy_name,
                    description=description,
                    parameters=parameters,
                )

            except Exception as e:
                logger.error(f"生成策略代码失败: {e}")
                assistant_response = f"抱歉，生成策略代码时出现错误：{str(e)}\n\n请尝试更详细地描述您的需求，或者换一个角度描述策略思路。"

        else:
            # 不生成代码，只是普通对话
            assistant_response = self._generate_conversational_response(user_message)

        # 7. 保存助手消息
        assistant_message_id = await self.conversation_service.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=assistant_response,
            generated_code=generated_code,
            strategy_version_id=strategy_version_id,
        )

        logger.info(f"助手消息保存成功: {assistant_message_id}")

        # 8. 更新策略版本的 message_id
        if strategy_version_id:
            await self.strategy_service.update_strategy_version(
                strategy_id=strategy_version_id,
                user_id=user_id,
                message_id=assistant_message_id,
            )

        # 9. 更新对话的当前策略ID
        if strategy_version_id:
            await self.conversation_service.update_conversation(
                conversation_id, user_id, current_strategy_id=strategy_version_id
            )

        return {
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id,
            "assistant_response": assistant_response,
            "generated_code": generated_code,
            "strategy_version_id": strategy_version_id,
        }

    async def improve_strategy(
        self,
        conversation_id: str,
        user_id: str,
        current_strategy_id: str,
        improvement_request: str,
        backtest_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        改进现有策略

        Args:
            conversation_id: 对话ID
            user_id: 用户ID
            current_strategy_id: 当前策略版本ID
            improvement_request: 改进需求
            backtest_results: 回测结果

        Returns:
            改进结果
        """
        # 1. 获取当前策略代码
        current_strategy = await self.strategy_service.get_strategy_version(
            current_strategy_id, user_id
        )

        if not current_strategy:
            raise ValueError("策略不存在")

        current_code = current_strategy["code"]

        # 2. 调用 AI 改进策略
        improvement_result = self.strategy_generator.improve_strategy(
            current_code=current_code,
            improvement_request=improvement_request,
            backtest_results=backtest_results,
        )

        improved_code = improvement_result["code"]

        # 3. 创建新的策略版本
        new_strategy_id = await self.strategy_service.create_strategy_version(
            strategy_name=current_strategy["strategy_name"],
            user_id=user_id,
            code=improved_code,
            conversation_id=conversation_id,
            message_id=None,
            strategy_type=current_strategy["strategy_type"],
            parameters=improvement_result.get("parameters", {}),
            version_description=f"改进版本：{improvement_request}",
        )

        # 4. 保存对话消息
        user_msg_id = await self.conversation_service.add_message(
            conversation_id, MessageRole.USER, improvement_request
        )

        assistant_response = f"""
已根据您的需求改进策略。

改进说明：
{improvement_request}

新版本策略已生成，您可以查看代码并进行回测。
"""

        assistant_msg_id = await self.conversation_service.add_message(
            conversation_id,
            MessageRole.ASSISTANT,
            assistant_response,
            generated_code=improved_code,
            strategy_version_id=new_strategy_id,
        )

        return {
            "user_message_id": user_msg_id,
            "assistant_message_id": assistant_msg_id,
            "improved_strategy_id": new_strategy_id,
            "improved_code": improved_code,
        }

    async def explain_strategy(
        self, strategy_id: str, user_id: str
    ) -> Dict[str, str]:
        """
        解释策略代码

        Args:
            strategy_id: 策略版本ID
            user_id: 用户ID

        Returns:
            解释文本
        """
        # 获取策略代码
        strategy = await self.strategy_service.get_strategy_version(
            strategy_id, user_id
        )

        if not strategy:
            raise ValueError("策略不存在")

        # 调用 AI 解释
        explanation = self.strategy_generator.explain_strategy(strategy["code"])

        return {"explanation": explanation}

    def _should_generate_code(self, user_message: str) -> bool:
        """
        判断是否应该生成代码

        Args:
            user_message: 用户消息

        Returns:
            是否需要生成代码
        """
        # 简单的关键词匹配
        generate_keywords = [
            "生成",
            "创建",
            "写一个",
            "帮我写",
            "策略",
            "代码",
            "实现",
            "开发",
            "编写",
        ]

        user_message_lower = user_message.lower()

        for keyword in generate_keywords:
            if keyword in user_message_lower:
                return True

        # 如果消息比较长（超过20个字），也可能是策略需求
        if len(user_message) > 20:
            return True

        return False

    def _format_assistant_response(
        self,
        strategy_name: str,
        description: str,
        parameters: Dict[str, Any],
    ) -> str:
        """
        格式化助手回复

        Args:
            strategy_name: 策略名称
            description: 策略描述
            parameters: 策略参数

        Returns:
            格式化的回复文本
        """
        response = f"""
我已经为您生成了策略代码。

**策略名称**: {strategy_name}

**策略说明**: {description}

**策略参数**:
"""

        if parameters:
            for param_name, param_value in parameters.items():
                response += f"- {param_name}: {param_value}\n"
        else:
            response += "（策略无可配置参数）\n"

        response += """
您可以查看生成的代码，并根据需要进行调整。

**下一步操作建议**:
1. 查看并理解策略代码
2. 运行回测查看策略表现
3. 根据回测结果优化参数或策略逻辑

如需修改策略，请告诉我具体的改进方向。
"""

        return response.strip()

    def _generate_conversational_response(self, user_message: str) -> str:
        """
        生成普通对话响应

        Args:
            user_message: 用户消息

        Returns:
            响应文本
        """
        # 简单的响应模板
        greeting_keywords = ["你好", "您好", "hi", "hello"]
        help_keywords = ["帮助", "怎么", "如何", "什么"]

        user_message_lower = user_message.lower()

        if any(kw in user_message_lower for kw in greeting_keywords):
            return """
您好！我是量化策略开发助手。

我可以帮助您：
- 生成量化交易策略代码
- 解释策略逻辑
- 优化策略表现

请描述您想开发的策略思路，我会为您生成相应的代码。
"""

        if any(kw in user_message_lower for kw in help_keywords):
            return """
我可以根据您的需求生成 Backtrader 量化交易策略代码。

您可以这样描述需求：
- "帮我写一个基于双均线的趋势策略"
- "生成一个 RSI 超买超卖策略"
- "创建一个网格交易策略"

请详细描述您的策略思路，包括：
1. 使用的技术指标
2. 交易信号条件
3. 风控措施（止损、止盈等）

我会为您生成完整可运行的策略代码。
"""

        return "请问您需要开发什么样的量化交易策略？请详细描述策略思路，我会为您生成代码。"


# 全局服务实例
ai_conversation_service = AIConversationService()
