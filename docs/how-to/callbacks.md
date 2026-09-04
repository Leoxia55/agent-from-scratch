# 使用 Callbacks

Callbacks 是 Agent loop 的扩展点，签名按阶段不同：

- `before_llm_callbacks(context, request)`：修改请求，或直接返回 `LlmResponse` 跳过模型调用。
- `before_tool_callbacks(context, tool_call)`：返回字符串/错误值可阻止工具执行；返回 `None` 则继续。
- `after_tool_callbacks(context, tool_result)`：记录、改写或替换工具结果。

```python
from scratchagent import Agent
from scratchagent.tools import approval_callback, search_compressor


async def add_trace(context, request):
    request.append_instructions(f"execution_id={context.execution_id}")


agent = Agent(
    model=client,
    before_llm_callbacks=[add_trace],
    before_tool_callbacks=[approval_callback],
    after_tool_callbacks=[search_compressor],
)
```

每个 callback 按注册顺序串行执行。`before_llm` callback 返回 `LlmResponse` 后会立即跳过剩余的 before-LLM callback 和模型调用；请确保返回对象包含可用的 `content`。不要在 callback 中阻塞事件循环或修改与其他并行 Agent 共享的可变对象。
