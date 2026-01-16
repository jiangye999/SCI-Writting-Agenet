"""
Model Router - Multi-Provider AI Model Router
支持通过本地API代理访问多个AI提供商
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

import requests


class TaskType(Enum):
    """任务类型枚举"""

    STYLE_ANALYSIS = "style_analysis"
    LITERATURE_IMPORT = "literature_import"
    INTRO_WRITING = "intro_writing"
    METHODS_WRITING = "methods_writing"
    RESULTS_WRITING = "results_writing"
    DISCUSSION_WRITING = "discussion_writing"
    INTEGRATION = "integration"
    CITATION_VALIDATION = "citation_validation"
    GENERAL = "general"


class Provider(Enum):
    """AI提供商枚举"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GOOGLE = "google"
    LOCAL = "local"


@dataclass
class ModelConfig:
    """模型配置"""

    name: str
    provider: Provider
    context_length: int = 128000
    max_output_tokens: int = 4096
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


@dataclass
class ModelResponse:
    """模型响应"""

    content: str
    model: str
    provider: Provider
    input_tokens: int
    output_tokens: int
    response_time: float
    cost: float


# 默认模型配置
DEFAULT_MODELS = {
    TaskType.STYLE_ANALYSIS: ModelConfig(
        name="gpt-4o",
        provider=Provider.OPENAI,
        context_length=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        strengths=["complex analysis", "pattern recognition", "nuanced understanding"],
        weaknesses=["cost"],
    ),
    TaskType.LITERATURE_IMPORT: ModelConfig(
        name="claude-sonnet-4",
        provider=Provider.ANTHROPIC,
        context_length=200000,
        max_output_tokens=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        strengths=[
            "structured extraction",
            "consistent formatting",
            "semantic understanding",
        ],
        weaknesses=["slower than alternatives"],
    ),
    TaskType.INTRO_WRITING: ModelConfig(
        name="deepseek-chat",
        provider=Provider.DEEPSEEK,
        context_length=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.00014,
        cost_per_1k_output=0.00028,
        strengths=["creative writing", "cost-effective", "coherent narratives"],
        weaknesses=["less precise for technical content"],
    ),
    TaskType.METHODS_WRITING: ModelConfig(
        name="claude-sonnet-4",
        provider=Provider.ANTHROPIC,
        context_length=200000,
        max_output_tokens=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        strengths=["technical precision", "structured output", "accurate terminology"],
        weaknesses=["cost"],
    ),
    TaskType.RESULTS_WRITING: ModelConfig(
        name="gpt-4o",
        provider=Provider.OPENAI,
        context_length=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        strengths=["numerical reasoning", "data interpretation", "analytical writing"],
        weaknesses=["cost"],
    ),
    TaskType.DISCUSSION_WRITING: ModelConfig(
        name="claude-3-5-sonnet",
        provider=Provider.ANTHROPIC,
        context_length=200000,
        max_output_tokens=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        strengths=["nuanced reasoning", "argumentation", "literature synthesis"],
        weaknesses=["cost"],
    ),
    TaskType.INTEGRATION: ModelConfig(
        name="claude-sonnet-4",
        provider=Provider.ANTHROPIC,
        context_length=200000,
        max_output_tokens=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        strengths=["thorough analysis", "consistency checking", "logical flow"],
        weaknesses=["cost"],
    ),
    TaskType.CITATION_VALIDATION: ModelConfig(
        name="deepseek-reasoner",
        provider=Provider.DEEPSEEK,
        context_length=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.0007,
        cost_per_1k_output=0.0007,
        strengths=["reasoning", "fact-checking", "cost-effective"],
        weaknesses=["less creative"],
    ),
    TaskType.GENERAL: ModelConfig(
        name="deepseek-chat",
        provider=Provider.DEEPSEEK,
        context_length=128000,
        max_output_tokens=4096,
        cost_per_1k_input=0.00014,
        cost_per_1k_output=0.00028,
        strengths=["general purpose", "cost-effective"],
        weaknesses=["less specialized"],
    ),
}

# 备用模型配置（用于故障转移）
FALLBACK_MODELS = {
    TaskType.STYLE_ANALYSIS: ["claude-3-5-sonnet", "gpt-4o-mini"],
    TaskType.LITERATURE_IMPORT: ["gpt-4o", "deepseek-chat"],
    TaskType.INTRO_WRITING: ["claude-3-5-sonnet", "gpt-4o-mini"],
    TaskType.METHODS_WRITING: ["gpt-4o", "claude-3-5-sonnet"],
    TaskType.RESULTS_WRITING: ["claude-3-5-sonnet", "claude-sonnet-4"],
    TaskType.DISCUSSION_WRITING: ["gpt-4o", "claude-sonnet-4"],
    TaskType.INTEGRATION: ["gpt-4o", "claude-3-5-sonnet"],
    TaskType.CITATION_VALIDATION: ["deepseek-chat", "gpt-4o-mini"],
}


class ModelRouter:
    """
    模型路由器 - 智能选择最佳模型处理任务
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:13148/v1",
        api_key: str = "",
        default_timeout: int = 120,
        enable_fallback: bool = True,
        max_retries: int = 2,
    ):
        """
        初始化模型路由器

        Args:
            base_url: 本地API代理基础URL
            api_key: API密钥（通过代理时通常不需要）
            default_timeout: 默认超时时间
            enable_fallback: 是否启用故障转移
            max_retries: 最大重试次数
        """
        print(f"[DEBUG] ModelRouter init received base_url='{base_url}'")
        self.base_url = base_url.rstrip("/")
        print(f"[DEBUG] ModelRouter init final base_url='{self.base_url}'")
        self.api_key = api_key
        self.default_timeout = default_timeout
        self.enable_fallback = enable_fallback
        self.max_retries = max_retries

        self.model_configs = DEFAULT_MODELS.copy()
        self.fallback_models = FALLBACK_MODELS.copy()

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_cost": 0.0,
            "total_tokens": 0,
            "average_response_time": 0.0,
        }

    def get_model_for_task(self, task_type: TaskType, **kwargs) -> ModelConfig:
        """
        根据任务类型获取最佳模型配置

        Args:
            task_type: 任务类型
            **kwargs: 覆盖配置（如 force_model="gpt-4o"）

        Returns:
            模型配置
        """
        # 强制使用指定模型
        if "force_model" in kwargs:
            return self._get_model_config_by_name(kwargs["force_model"])

        # 检查缓存的偏好（可选功能）
        if "use_preferred" in kwargs and kwargs["use_preferred"]:
            preferred = self._get_preferred_model(task_type)
            if preferred:
                return preferred

        return self.model_configs.get(task_type, self.model_configs[TaskType.GENERAL])

    def _get_model_config_by_name(self, model_name: str) -> ModelConfig:
        """根据模型名称获取配置"""
        for config in self.model_configs.values():
            if config.name == model_name:
                return config
        return ModelConfig(name=model_name, provider=Provider.LOCAL)

    def _get_preferred_model(self, task_type: TaskType) -> Optional[ModelConfig]:
        """获取首选模型（可扩展为学习用户偏好）"""
        return None

    def call_model(
        self,
        model_config: ModelConfig,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> ModelResponse:
        """
        调用模型

        Args:
            model_config: 模型配置
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大输出token
            **kwargs: 其他参数

        Returns:
            模型响应
        """
        start_time = time.time()

        # 设置默认值
        if temperature is None:
            temperature = 0.7 if "writing" in model_config.name else 0.3
        if max_tokens is None:
            max_tokens = model_config.max_output_tokens

        # 构建请求
        print(f"[DEBUG] call_model: self.base_url='{self.base_url}'")
        url = f"{self.base_url}/chat/completions"
        print(f"[DEBUG] call_model: final url='{url}'")

        # 根据提供商构建请求
        if model_config.provider == Provider.OPENAI:
            payload = {
                "model": model_config.name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        elif model_config.provider == Provider.ANTHROPIC:
            # Anthropic使用不同的格式
            payload = {
                "model": model_config.name,
                "messages": messages,
                "max_tokens": max_tokens,
            }
            if temperature is not None:
                payload["temperature"] = temperature
        elif model_config.provider == Provider.DEEPSEEK:
            payload = {
                "model": model_config.name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        else:
            # 通用格式
            payload = {
                "model": model_config.name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # 发送请求
        response = None
        error = None

        for attempt in range(self.max_retries):
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.default_timeout,
                )
                resp.raise_for_status()
                response = resp.json()
                break
            except requests.exceptions.RequestException as e:
                error = e
                if attempt < self.max_retries - 1:
                    time.sleep(1)  # 重试前等待
                continue

        # 处理响应
        end_time = time.time()
        response_time = end_time - start_time

        if response is None:
            self.stats["failed_requests"] += 1
            raise Exception(f"模型调用失败: {error}")

        # 解析响应
        content, input_tokens, output_tokens, cost = self._parse_response(
            response, model_config, messages
        )

        # 更新统计
        self.stats["total_requests"] += 1
        self.stats["successful_requests"] += 1
        self.stats["total_cost"] += cost
        self.stats["total_tokens"] += input_tokens + output_tokens

        # 更新平均响应时间
        total = self.stats["successful_requests"]
        current_avg = self.stats["average_response_time"]
        self.stats["average_response_time"] = (
            current_avg * (total - 1) + response_time
        ) / total

        return ModelResponse(
            content=content,
            model=model_config.name,
            provider=model_config.provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            response_time=response_time,
            cost=cost,
        )

    def _parse_response(
        self, response: Dict, model_config: ModelConfig, messages: List[Dict[str, str]]
    ) -> Tuple[str, int, int, float]:
        """
        解析模型响应

        Args:
            response: API响应
            model_config: 模型配置
            messages: 原始消息

        Returns:
            (内容, 输入token数, 输出token数, 成本)
        """
        # OpenAI格式
        if "choices" in response:
            choice = response["choices"][0]
            content = choice.get("message", {}).get("content", "")

            usage = response.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            # 计算成本
            cost = (
                input_tokens / 1000 * model_config.cost_per_1k_input
                + output_tokens / 1000 * model_config.cost_per_1k_output
            )

            return content, input_tokens, output_tokens, cost

        # 其他格式（简化处理）
        content = response.get("content", str(response))
        input_tokens = len(str(messages)) // 4  # 估算
        output_tokens = len(content) // 4  # 估算
        cost = (
            input_tokens / 1000 * model_config.cost_per_1k_input
            + output_tokens / 1000 * model_config.cost_per_1k_output
        )

        return content, input_tokens, output_tokens, cost

    def process_task(
        self,
        task_type: TaskType,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> ModelResponse:
        """
        处理任务

        Args:
            task_type: 任务类型
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度
            **kwargs: 其他参数

        Returns:
            模型响应
        """
        # 获取最佳模型
        model_config = self.get_model_for_task(task_type, **kwargs)

        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # 调用模型
        return self.call_model(model_config, messages, temperature, **kwargs)

    def process_with_fallback(
        self,
        task_type: TaskType,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> ModelResponse:
        """
        使用故障转移处理任务

        Args:
            task_type: 任务类型
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 其他参数

        Returns:
            模型响应
        """
        if not self.enable_fallback:
            return self.process_task(task_type, prompt, system_prompt, **kwargs)

        # 首选模型
        model_config = self.get_model_for_task(task_type, **kwargs)

        try:
            return self.call_model(
                model_config, self._build_messages(system_prompt, prompt), **kwargs
            )
        except Exception as e:
            print(f"[WARNING] Primary model {model_config.name} failed: {e}")
            print(f"[INFO] Trying fallback models...")

            # 尝试备用模型
            fallbacks = self.fallback_models.get(task_type, [])

            for fallback_model in fallbacks:
                try:
                    fallback_config = self._get_model_config_by_name(fallback_model)
                    return self.call_model(
                        fallback_config,
                        self._build_messages(system_prompt, prompt),
                        **kwargs,
                    )
                except Exception as fallback_error:
                    print(
                        f"[WARNING] Fallback model {fallback_model} failed: {fallback_error}"
                    )
                    continue

            raise Exception("All models failed")

    def _build_messages(
        self, system_prompt: Optional[str], user_prompt: str
    ) -> List[Dict[str, str]]:
        """构建消息列表"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def get_statistics(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            **self.stats,
            "average_cost_per_request": (
                self.stats["total_cost"] / self.stats["total_requests"]
                if self.stats["total_requests"] > 0
                else 0
            ),
            "success_rate": (
                self.stats["successful_requests"] / self.stats["total_requests"]
                if self.stats["total_requests"] > 0
                else 0
            ),
        }

    def estimate_cost(self, task_type: TaskType, estimated_tokens: int) -> float:
        """
        估算任务成本

        Args:
            task_type: 任务类型
            estimated_tokens: 估计的token数

        Returns:
            估计成本
        """
        model_config = self.get_model_for_task(task_type)
        return (
            estimated_tokens
            / 1000
            * (model_config.cost_per_1k_input + model_config.cost_per_1k_output)
        )


# 便捷函数
def create_router(**kwargs) -> ModelRouter:
    """创建路由器实例"""
    return ModelRouter(**kwargs)


def process_with_optimal_model(
    task_type: TaskType,
    prompt: str,
    base_url: str = "http://127.0.0.1:13148/v1",
    **kwargs,
) -> ModelResponse:
    """
    使用最佳模型处理任务

    Args:
        task_type: 任务类型
        prompt: 提示
        base_url: API基础URL
        **kwargs: 其他参数

    Returns:
        模型响应
    """
    router = ModelRouter(base_url=base_url)
    return router.process_task(task_type, prompt, **kwargs)


if __name__ == "__main__":
    # 测试代码
    router = ModelRouter()

    # 测试不同任务
    test_tasks = [
        (
            TaskType.INTRO_WRITING,
            "Write an introduction for a paper about AI in healthcare.",
        ),
        (
            TaskType.METHODS_WRITING,
            "Write methods section for a machine learning study.",
        ),
    ]

    for task_type, prompt in test_tasks:
        try:
            response = router.process_task(task_type, prompt)
            print(f"\n[Task: {task_type.value}]")
            print(f"Model: {response.model}")
            print(f"Cost: ${response.cost:.4f}")
            print(f"Response time: {response.response_time:.2f}s")
            print(f"Content preview: {response.content[:100]}...")
        except Exception as e:
            print(f"\n[Task: {task_type.value}] Failed: {e}")

    # 打印统计
    print("\n" + "=" * 50)
    print("Statistics:")
    for key, value in router.get_statistics().items():
        print(f"  {key}: {value}")
