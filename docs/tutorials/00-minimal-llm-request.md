# 00. 最小 LLM 请求

目标：先使用 `LlmClient` 发送一次请求，确认 provider、模型和环境变量都可用，再创建 Agent。

## 1. 配置 provider

ScratchAgent 通过 `resolve_model_config` 从 `Provider` 和环境变量生成不可变的 `ModelConfig`。OpenAI-compatible provider 需要 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`。

```powershell
$env:OPENAI_API_KEY = "your-key"
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"
```

## 2. 调用客户端

```python
import asyncio

from scratchagent.llm import LlmClient, Provider, resolve_model_config


async def main() -> None:
    config = resolve_model_config(
        provider=Provider.OPENAI_COMPAT,
        model="gpt-4o-mini",
    )
    client = LlmClient(default_config=config)
    response = await client.ask("用一句话解释什么是智能体。")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
```

`ask()` 是高层便捷接口，返回第一个文本消息。底层 `generate()` 接收 `LlmRequest`，返回 `LlmResponse`，并保留工具调用和 usage metadata。

## 3. 运行与排错

```powershell
uv run python minimal_request.py
```

- `LLMConfigError`：检查对应 provider 的必填环境变量。
- `LlmResponse.error_message` 非空：请求已经被客户端捕获，先打印错误再处理。
- 模型名称带 `openai/`、`anthropic/`、`lm_studio/` 等前缀时，解析器会去掉已知前缀后重新拼接。

下一步：[工具 Agent](01-tool-agent.md)。

