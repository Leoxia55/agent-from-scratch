"""
LiteLLM SDK 封装工具的提供商配置助手

该模块使提供商路由保持显式。每个请求都配有独立的模型前缀、
API 密钥以及 API 基础地址，而非依赖 LiteLLM 全局状态。
"""

import os
from dataclasses import dataclass
from enum import StrEnum
from dotenv import find_dotenv, load_dotenv

class LLMConfigError(RuntimeError):
    """当提供商缺少必需的环境配置项时抛出该异常."""


class UnsupportedProviderError(ValueError):
    """当提供商的值无法映射到 LiteLLM 时触发."""


class Provider(StrEnum):
    """受此封装程序支持的提供方列表。"""

    OPENAI_COMPAT = "openai_compat"
    ANTHROPIC = "anthropic"
    LLAMA = "llama_cpp"
    LM_STUDIO = "lm_studio"


@dataclass(frozen=True)
class ModelConfig:
    """已解析单个模型端点的 LiteLLM 调用设置。"""

    provider: Provider
    model: str
    api_key: str | None = None
    api_base: str | None = None
    use_chat_completions_api: bool = False


def load_project_env() -> None:
    """加载最近的.env 文件，且不暴露或覆盖已有变量值。

    已存在的进程环境变量优先级高于.env 文件内的变量。
    此举可保证测试、持续集成以及手动导出的 Shell 变量结果可复现。
    """

    env_file = find_dotenv(usecwd=True)
    if env_file:
        load_dotenv(env_file, override=False)


def resolve_provider(provider: Provider | str) -> Provider:
    """将字符串或服务商枚举值转换为受支持的服务商。"""

    if isinstance(provider, Provider):
        return provider
    try:
        return Provider(provider)
    except ValueError as exc:
        supported = ", ".join(item.value for item in Provider)
        raise UnsupportedProviderError(
            f"Unsupported provider {provider!r}. Supported providers: {supported}."
        ) from exc


def resolve_model_config(provider: Provider | str, model: str) -> ModelConfig:
    """解析 LiteLLM 针对服务商‑模型组合的模型前缀与凭证信息."""

    load_project_env()
    resolved_provider = resolve_provider(provider)
    clean_model = _strip_known_prefix(model)

    if resolved_provider is Provider.OPENAI_COMPAT:
        return ModelConfig(
            provider=resolved_provider,
            model=f"openai/{clean_model}",
            api_key=_require_env("OPENAI_API_KEY", "OpenAI-compatible relay"),
            api_base=_require_env("OPENAI_BASE_URL", "OpenAI-compatible relay"),
        )

    if resolved_provider is Provider.ANTHROPIC:
        return ModelConfig(
            provider=resolved_provider,
            model=f"anthropic/{clean_model}",
            api_key=_require_env("ANTHROPIC_API_KEY", "Anthropic relay"),
            api_base=_require_first_env(
                ("ANTHROPIC_BASE_URL", "ANTHROPIC_API_BASE"), "Anthropic relay"
            ),
        )

    if resolved_provider is Provider.LLAMA:
        return ModelConfig(
            provider=resolved_provider,
            model=f"openai/{clean_model}",
            api_key=_optional_env("LLAMA_API_KEY") or "dummy-key",
            api_base=_optional_env("LLAMA_BASE_URL") or "http://127.0.0.1:8080/v1",
            use_chat_completions_api=True,
        )

    if resolved_provider is Provider.LM_STUDIO:
        return ModelConfig(
            provider=resolved_provider,
            model=f"lm_studio/{clean_model}",
            api_key=_optional_env("LM_STUDIO_API_KEY"),
            api_base=_require_first_env(
                ("LM_STUDIO_API_BASE", "LM_STUDIO_BASE_URL"), "LM Studio"
            ),
            use_chat_completions_api=True,
        )

    raise UnsupportedProviderError(f"Unsupported provider {resolved_provider!r}.")


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else None


def _require_env(name: str, provider_name: str) -> str:
    value = _optional_env(name)
    if value is None:
        raise LLMConfigError(f"{provider_name} requires environment variable {name}.")
    return value


def _require_first_env(names: tuple[str, ...], provider_name: str) -> str:
    for name in names:
        value = _optional_env(name)
        if value is not None:
            return value
    joined = " or ".join(names)
    raise LLMConfigError(f"{provider_name} requires environment variable {joined}.")


def _strip_known_prefix(model: str) -> str:
    """允许调用方传入原始模型名称或者带有 LiteLLM 前缀的模型名称。"""

    known_prefixes = ("openai/", "anthropic/", "hosted_vllm/", "lm_studio/")
    for prefix in known_prefixes:
        if model.startswith(prefix):
            return model.removeprefix(prefix)
    return model


