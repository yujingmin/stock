"""
策略代码生成器
"""
from typing import List, Dict, Any, Optional
from app.services.ai.claude_client import ClaudeClient
from app.services.strategy.templates import get_all_templates, get_template_by_type


class StrategyGenerator:
    """策略代码生成器"""

    def __init__(self):
        """初始化生成器"""
        self.claude_client = ClaudeClient()

    def generate_strategy(
        self,
        user_requirement: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        strategy_type: Optional[str] = None,
        use_template: bool = True,
    ) -> Dict[str, Any]:
        """
        生成策略代码

        Args:
            user_requirement: 用户需求描述
            conversation_history: 对话历史
            strategy_type: 策略类型（trend, grid, mean_reversion等）
            use_template: 是否使用模板

        Returns:
            {
                "code": "生成的策略代码",
                "strategy_name": "策略名称",
                "strategy_type": "策略类型",
                "description": "策略描述",
                "parameters": {...}  # 策略参数说明
            }
        """
        # 1. 构建上下文
        context = self._build_context(conversation_history)

        # 2. 获取相关模板（如果使用）
        examples = []
        if use_template:
            if strategy_type:
                template = get_template_by_type(strategy_type)
                if template:
                    examples.append(template["code"])
            else:
                # 获取所有模板作为示例
                templates = get_all_templates()
                examples = [t["code"] for t in templates[:2]]  # 只取前2个

        # 3. 构建详细的 Prompt
        prompt = self._build_prompt(user_requirement, strategy_type)

        # 4. 调用 AI 生成代码
        generated_code = self.claude_client.generate_code(
            prompt=prompt, context=context, examples=examples if examples else None
        )

        # 5. 提取代码和元数据
        result = self._parse_generated_code(generated_code, user_requirement)

        return result

    def improve_strategy(
        self,
        current_code: str,
        improvement_request: str,
        backtest_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        改进现有策略

        Args:
            current_code: 当前策略代码
            improvement_request: 改进需求
            backtest_results: 回测结果（可选）

        Returns:
            改进后的策略信息
        """
        if backtest_results:
            # 基于回测结果优化
            optimized_code = self.claude_client.optimize_strategy(
                code=current_code, performance_metrics=backtest_results
            )
        else:
            # 基于用户需求改进
            system_prompt = """你是一个量化交易策略改进专家。
请根据用户的改进需求，修改现有策略代码。

改进原则：
1. 保持原有策略的核心逻辑
2. 针对性优化用户关注的问题
3. 确保代码可运行
4. 添加必要的注释说明改进点

请只返回改进后的完整策略代码。
"""

            user_message = f"""
当前策略代码：
```python
{current_code}
```

用户改进需求：
{improvement_request}

请改进这个策略。
"""

            messages = [{"role": "user", "content": user_message}]

            optimized_code = self.claude_client.chat(
                messages=messages, system=system_prompt
            )

        result = self._parse_generated_code(optimized_code, improvement_request)
        return result

    def explain_strategy(self, code: str) -> str:
        """
        解释策略代码

        Args:
            code: 策略代码

        Returns:
            策略解释文本
        """
        system_prompt = """你是一个量化交易策略解读专家。
请用通俗易懂的语言解释策略代码的逻辑和原理。

解释内容包括：
1. 策略核心思想
2. 使用的技术指标
3. 交易信号生成逻辑
4. 风控措施
5. 适用场景和风险提示

请用中文解释，分点说明，每点不超过3句话。
"""

        user_message = f"""
请解释以下策略代码：

```python
{code}
```
"""

        messages = [{"role": "user", "content": user_message}]

        return self.claude_client.chat(messages=messages, system=system_prompt)

    def _build_context(
        self, conversation_history: Optional[List[Dict[str, str]]]
    ) -> Optional[str]:
        """
        构建对话上下文

        Args:
            conversation_history: 对话历史

        Returns:
            格式化的上下文字符串
        """
        if not conversation_history:
            return None

        context_lines = []
        for msg in conversation_history[-5:]:  # 只取最近5条
            role = "用户" if msg["role"] == "user" else "助手"
            context_lines.append(f"{role}: {msg['content']}")

        return "\n".join(context_lines)

    def _build_prompt(self, user_requirement: str, strategy_type: Optional[str]) -> str:
        """
        构建详细的生成 Prompt

        Args:
            user_requirement: 用户需求
            strategy_type: 策略类型

        Returns:
            详细的 Prompt
        """
        type_hints = {
            "trend": "趋势跟踪策略，使用均线、MACD等指标捕捉趋势",
            "grid": "网格交易策略，在价格区间内高抛低吸",
            "mean_reversion": "均值回归策略，使用RSI等指标捕捉超买超卖",
            "arbitrage": "套利策略，利用价格差异获利",
            "momentum": "动量策略，追踪价格动量和成交量变化",
        }

        prompt = f"""
请根据以下需求生成一个 Backtrader 量化交易策略：

用户需求：
{user_requirement}
"""

        if strategy_type and strategy_type in type_hints:
            prompt += f"""
策略类型：{strategy_type}
类型说明：{type_hints[strategy_type]}
"""

        prompt += """
代码要求：
1. 完整的 Backtrader Strategy 类
2. 包含 __init__、next、notify_order、notify_trade 等必要方法
3. 使用合理的技术指标
4. 实现止损止盈逻辑
5. 添加详细的中文注释
6. 定义可调整的策略参数（params）

数据接口说明：
- 使用 akshare 库获取 A 股数据
- K线数据字段：日期、开盘、收盘、最高、最低、成交量
- 已有常用技术指标：SMA、EMA、RSI、MACD、Bollinger Bands、ATR等

请生成完整可运行的策略代码。
"""

        return prompt

    def _parse_generated_code(
        self, generated_text: str, requirement: str
    ) -> Dict[str, Any]:
        """
        解析生成的代码文本

        Args:
            generated_text: AI 生成的文本
            requirement: 用户需求

        Returns:
            结构化的策略信息
        """
        # 提取代码块
        code = self._extract_code_from_text(generated_text)

        # 尝试提取策略名称
        strategy_name = self._extract_strategy_name(code)
        if not strategy_name:
            strategy_name = "CustomStrategy"

        # 生成策略描述
        description = self._generate_description(requirement)

        # 提取参数（基于代码分析）
        parameters = self._extract_parameters(code)

        return {
            "code": code,
            "strategy_name": strategy_name,
            "strategy_type": "custom",
            "description": description,
            "parameters": parameters,
        }

    def _extract_code_from_text(self, text: str) -> str:
        """
        从文本中提取代码块

        Args:
            text: 包含代码的文本

        Returns:
            纯代码字符串
        """
        import re

        # 尝试提取 ```python ... ``` 代码块
        pattern = r"```python\s*(.*?)\s*```"
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            return matches[0].strip()

        # 尝试提取 ``` ... ``` 代码块
        pattern = r"```\s*(.*?)\s*```"
        matches = re.findall(pattern, text, re.DOTALL)

        if matches:
            return matches[0].strip()

        # 如果没有代码块标记，返回全部内容
        return text.strip()

    def _extract_strategy_name(self, code: str) -> Optional[str]:
        """
        从代码中提取策略类名

        Args:
            code: 策略代码

        Returns:
            策略类名
        """
        import re

        # 匹配 class StrategyName(bt.Strategy):
        pattern = r"class\s+(\w+)\s*\("
        match = re.search(pattern, code)

        if match:
            return match.group(1)

        return None

    def _extract_parameters(self, code: str) -> Dict[str, Any]:
        """
        从代码中提取策略参数

        Args:
            code: 策略代码

        Returns:
            参数字典
        """
        import re

        parameters = {}

        # 匹配 params = (('param_name', default_value),)
        pattern = r"params\s*=\s*\((.*?)\)"
        match = re.search(pattern, code, re.DOTALL)

        if match:
            params_text = match.group(1)
            # 匹配每个参数
            param_pattern = r"\('(\w+)',\s*([^)]+)\)"
            params = re.findall(param_pattern, params_text)

            for param_name, param_value in params:
                try:
                    # 尝试评估参数值
                    parameters[param_name] = eval(param_value.strip())
                except:
                    parameters[param_name] = param_value.strip()

        return parameters

    def _generate_description(self, requirement: str) -> str:
        """
        生成策略描述

        Args:
            requirement: 用户需求

        Returns:
            策略描述
        """
        # 简单处理：取需求的前100个字符
        if len(requirement) > 100:
            return requirement[:100] + "..."
        return requirement
