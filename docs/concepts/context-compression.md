# 上下文压缩

上下文优化解决的是 token 上限、成本和延迟之间的平衡，而不是把历史“变得更正确”。内置策略按信息损失从低到高大致为：

1. `apply_compaction`：删除或截断已知工具参数和结果中的冗余内容。
2. `apply_sliding_window`：保留首条用户消息和最近窗口。
3. `apply_summarization`：调用 LLM 把旧内容替换为 `SummaryMessage`。

`ContextOptimizer` 在 `before_llm` 阶段统计 `count_tokens(request)`；超过阈值后先压缩，再在仍超限时摘要。摘要不是可逆操作，适合已经完成的早期步骤；最近的工具调用和最终答案应保留。

自定义 callback 时只修改当前 request 或明确要替换的 context events，避免在并行 workflow 中重排其他 Agent 的事件。阈值应通过真实 usage metadata 校准，而不是照搬默认的 50,000。

