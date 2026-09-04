# LLM 参考

导入：`from scratchagent.llm import LlmClient, LlmRequest, LlmResponse, ModelConfig, Provider`

## `LlmClient`

```python
client = LlmClient(default_config: ModelConfig | None = None)
response = await client.generate(request: LlmRequest)
text = await client.ask(prompt: str, response_format: type[BaseModel] | None = None)
```

`generate()` 将 instructions 转为 system message，将 `Message`、`ToolCall`、`ToolResult` 和 `SummaryMessage` 转为 provider 的 chat messages；工具定义来自 `BaseTool.tool_definition`。请求异常会包装为 `LlmResponse(error_message=...)`。

`ask()` 适合纯文本或结构化响应。传入 Pydantic `response_format` 时，客户端要求模型只返回 JSON，并用 `model_validate_json` 校验；代码围栏会被剥掉。

## `ModelConfig` 和 `Provider`

`ModelConfig` 是不可变配置对象：

| 字段 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `provider` | `Provider` | 必填 | 使用的模型供应商 |
| `model` | `str` | 必填 | provider 的模型名 |
| `api_key` | `str | None` | `None` | 显式 API key；省略时从环境变量读取 |
| `api_base` | `str | None` | `None` | 自定义 API 地址 |
| `use_chat_completions_api` | `bool` | `False` | 是否使用兼容 Chat Completions 的请求路径 |

`Provider` 当前包含 `OPENAI_COMPAT`、`ANTHROPIC`、`LLAMA` 和 `LM_STUDIO`。使用字符串配置时，可通过 `resolve_model_config()` 将 provider、模型名和环境变量解析成 `ModelConfig`；未知 provider 会抛出 `UnsupportedProviderError`，缺少必要配置会抛出 `LLMConfigError`。

## `LlmRequest`

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `instructions` | `list[str]` | system 指令 |
| `contents` | `list[ContentItem]` | 对话、工具调用和结果 |
| `tools` | `list[BaseTool]` | 发送给模型的工具 |
| `tool_choice` | `str | None` | `auto`、`required` 或 provider 支持的值 |
| `model_id` | `str | None` | 覆盖默认模型名称，provider 仍沿用默认配置 |

## `LlmResponse`

包含 `content: list[ContentItem]`、可选 `error_message` 和 `usage_metadata`（prompt/completion token 等）。
