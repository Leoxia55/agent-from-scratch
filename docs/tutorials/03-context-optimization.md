# 03. 上下文优化

长会话会同时推高 token 成本和模型延迟。ScratchAgent 提供滑动窗口、压缩和摘要三种机制，以及可组合的 `ContextOptimizer` callback。

## 1. 直接使用优化器

```python
from scratchagent.memory import ContextOptimizer

optimizer = ContextOptimizer(
    llm_client=client,
    token_threshold=12_000,
    enable_compaction=True,
    enable_summarization=True,
    keep_recent_steps=5,
)
agent = Agent(model=client, before_llm_callbacks=[optimizer])
```

callback 在每次 LLM 请求前接收 `(context, request)`。超过阈值时，先做规则化压缩；仍然超限时，把较早事件交给 LLM 生成 `SummaryMessage`，保留最近步骤。

## 2. 选择更可控的策略

```python
from scratchagent.memory import apply_sliding_window

agent = Agent(
    model=client,
    before_llm_callbacks=[
        lambda context, request: apply_sliding_window(
            context, request, window_size=20
        )
    ],
)
```

滑动窗口始终保留第一条用户消息和最近内容，适合不需要摘要的对话。`apply_compaction` 会缩短 `create_file` 参数以及文件/搜索工具结果；`apply_summarization` 需要额外 LLM 调用。

## 3. 调参建议

- 先用 `count_tokens(request)` 记录真实 token，再设阈值。
- 需要可追溯原文时关闭摘要，只使用窗口或压缩。
- 保留最近步骤数应覆盖“最后一次工具调用 + 最终回答”的完整链路。
- 优化器修改的是本次 `LlmRequest`；摘要内容来自上下文事件，但不会自动改写已保存的 `context.events`。不要在 callback 中无意清空 `context.state`。

下一步：[E2B 与 Skills](04-e2b-and-skills.md)。
