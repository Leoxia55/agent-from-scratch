"""llm/_config.py 单元测试：Provider 与模型配置解析。"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from scratchagent.llm import (
    LLMConfigError,
    ModelConfig,
    Provider,
    UnsupportedProviderError,
    resolve_model_config,
)
from scratchagent.llm._config import resolve_provider


# ---------------------------------------------------------------- resolve_provider
class TestResolveProvider:
    def test_enum_passthrough(self):
        assert resolve_provider(Provider.ANTHROPIC) is Provider.ANTHROPIC

    def test_str(self):
        assert resolve_provider("anthropic") is Provider.ANTHROPIC

    def test_unsupported(self):
        with pytest.raises(UnsupportedProviderError):
            resolve_provider("foo")


# ---------------------------------------------------------------- resolve_model_config
class TestResolveModelConfig:
    def test_openai_compat(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://relay.example/v1")
        cfg = resolve_model_config(Provider.OPENAI_COMPAT, "gpt-4o-mini")
        assert cfg.provider is Provider.OPENAI_COMPAT
        assert cfg.model == "openai/gpt-4o-mini"
        assert cfg.api_key == "sk-test"
        assert cfg.api_base == "https://relay.example/v1"

    def test_anthropic(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant")
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://ant.example")
        cfg = resolve_model_config(Provider.ANTHROPIC, "claude-3-5-sonnet")
        assert cfg.model == "anthropic/claude-3-5-sonnet"
        assert cfg.api_key == "sk-ant"
        assert cfg.api_base == "https://ant.example"

    def test_llama_defaults(self, monkeypatch):
        # 清空可能存在的 env
        for k in ("LLAMA_API_KEY", "LLAMA_BASE_URL"):
            monkeypatch.delenv(k, raising=False)
        cfg = resolve_model_config(Provider.LLAMA, "my-model")
        assert cfg.model == "openai/my-model"
        assert cfg.api_key == "dummy-key"
        assert cfg.api_base == "http://127.0.0.1:8080/v1"
        assert cfg.use_chat_completions_api is True

    def test_lm_studio(self, monkeypatch):
        monkeypatch.setenv("LM_STUDIO_API_BASE", "http://localhost:1234/v1")
        cfg = resolve_model_config(Provider.LM_STUDIO, "model-x")
        assert cfg.model == "lm_studio/model-x"
        assert cfg.api_base == "http://localhost:1234/v1"
        assert cfg.use_chat_completions_api is True

    def test_missing_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        with pytest.raises(LLMConfigError):
            resolve_model_config(Provider.OPENAI_COMPAT, "gpt-4o-mini")

    def test_strips_prefix(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://relay.example/v1")
        cfg = resolve_model_config(Provider.OPENAI_COMPAT, "openai/gpt-4")
        assert cfg.model == "openai/gpt-4"

    def test_model_config_frozen(self):
        cfg = ModelConfig(provider=Provider.LLAMA, model="m")
        with pytest.raises(FrozenInstanceError):
            cfg.model = "other"  # type: ignore[misc]


# ---------------------------------------------------------------- 异常类型
class TestErrors:
    def test_llm_config_error_is_runtime_error(self):
        assert issubclass(LLMConfigError, RuntimeError)

    def test_unsupported_provider_error_is_value_error(self):
        assert issubclass(UnsupportedProviderError, ValueError)
