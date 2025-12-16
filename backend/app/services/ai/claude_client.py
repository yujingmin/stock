"""
Claude API 客户端
"""
import anthropic
from typing import List, Dict, Any, Optional
from app.core.config import settings


class ClaudeClient:
    """Claude API 客户端封装"""

    def __init__(self):
        """初始化 Claude 客户端"""
        if not settings.CLAUDE_API_KEY:
            raise ValueError("CLAUDE_API_KEY 未配置")

        self.client = anthropic.Anthropic(
            api_key=settings.CLAUDE_API_KEY,
            base_url=settings.CLAUDE_API_BASE_URL
        )
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS
        self.temperature = settings.CLAUDE_TEMPERATURE

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表，格式 [{"role": "user"|"assistant", "content": "..."}]
            system: 系统提示词
            max_tokens: 最大生成 token 数
            temperature: 温度参数 (0-1)

        Returns:
            助手回复内容
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=system if system else None,
                messages=messages,
            )

            # 提取文本内容
            if response.content:
                return response.content[0].text
            return ""

        except anthropic.APIError as e:
            raise Exception(f"Claude API 错误: {e}")
        except Exception as e:
            raise Exception(f"调用 Claude API 失败: {e}")

    def generate_code(
        self,
        prompt: str,
        context: Optional[str] = None,
        examples: Optional[List[str]] = None,
    ) -> str:
        """
        生成代码

        Args:
            prompt: 用户需求描述
            context: 上下文信息（如历史对话）
            examples: 代码示例

        Returns:
            生成的代码
        """
        system_prompt = """你是一个专业的量化交易策略开发助手。
你的任务是根据用户需求生成 Python 量化交易策略代码。

代码要求：
1. 基于 Backtrader 框架
2. 代码清晰、注释详细
3. 包含策略逻辑、参数说明、风控措施
4. 遵循 Python PEP 8 编码规范
5. 确保代码可直接运行

请只返回策略代码，不要包含其他解释文字。
"""

        # 构建用户消息
        user_message = prompt

        if context:
            user_message = f"对话历史：\n{context}\n\n用户需求：\n{prompt}"

        if examples:
            examples_text = "\n\n".join(
                [f"示例 {i+1}:\n{ex}" for i, ex in enumerate(examples)]
            )
            user_message = f"{user_message}\n\n参考示例：\n{examples_text}"

        messages = [{"role": "user", "content": user_message}]

        return self.chat(messages=messages, system=system_prompt)

    def analyze_strategy(self, code: str, requirements: str) -> Dict[str, Any]:
        """
        分析策略代码

        Args:
            code: 策略代码
            requirements: 用户需求

        Returns:
            分析结果（合规性、建议等）
        """
        system_prompt = """你是一个量化交易策略审查专家。
请分析策略代码的质量、合规性和风险。

分析维度：
1. 代码质量（语法、逻辑、可读性）
2. 策略合理性（指标使用、交易逻辑）
3. 风险控制（止损、仓位管理）
4. 性能优化建议

请以 JSON 格式返回分析结果。
"""

        user_message = f"""
用户需求：
{requirements}

策略代码：
```python
{code}
```

请分析这段代码。
"""

        messages = [{"role": "user", "content": user_message}]

        response = self.chat(messages=messages, system=system_prompt)

        # 尝试解析 JSON
        try:
            import json
            return json.loads(response)
        except:
            return {"raw_analysis": response}

    def optimize_strategy(
        self, code: str, performance_metrics: Dict[str, Any]
    ) -> str:
        """
        优化策略代码

        Args:
            code: 原始策略代码
            performance_metrics: 回测性能指标

        Returns:
            优化后的策略代码
        """
        system_prompt = """你是一个量化交易策略优化专家。
根据回测结果优化策略代码，提升性能和稳定性。

优化方向：
1. 调整策略参数
2. 优化交易信号
3. 改进风控措施
4. 提升代码性能

请只返回优化后的策略代码。
"""

        user_message = f"""
当前策略代码：
```python
{code}
```

回测性能：
{performance_metrics}

请优化这个策略。
"""

        messages = [{"role": "user", "content": user_message}]

        return self.chat(messages=messages, system=system_prompt)
