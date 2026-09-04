# 切换 Provider

统一入口是 `resolve_model_config(provider, model)`。它从 `.env` 或进程环境读取凭据，并返回冻结的 `ModelConfig`。

## OpenAI-compatible

```dotenv
OPENAI_API_KEY=...
OPENAI_BASE_URL=https://api.openai.com/v1
```

```python
config = resolve_model_config(Provider.OPENAI_COMPAT, "gpt-4o-mini")
```

OpenRouter 等兼容接口可把自己的 base URL 和 key 放进 `OPENAI_*`，模型名按服务商要求传入。

## Anthropic

```dotenv
ANTHROPIC_API_KEY=...
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

```python
config = resolve_model_config(Provider.ANTHROPIC, "claude-3-5-sonnet-latest")
```

## 本地模型

Llama.cpp：

```dotenv
LLAMA_BASE_URL=http://127.0.0.1:8080/v1
LLAMA_API_KEY=dummy-key
```

```python
config = resolve_model_config(Provider.LLAMA, "my-model")
```

LM Studio：

```dotenv
LM_STUDIO_API_BASE=http://127.0.0.1:1234/v1
LM_STUDIO_API_KEY=optional
```

```python
config = resolve_model_config(Provider.LM_STUDIO, "local-model")
```

`Provider` 也接受字符串值，例如 `"anthropic"`。未知 provider 或缺少必填变量时会抛出配置错误；不要把 key 硬编码进源码。

