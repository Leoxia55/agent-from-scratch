# Agent Loop

`Agent.run()` 是一次完整执行；`Agent.step()` 是一次“请求模型并处理当前响应”的最小循环。核心状态集中在 `ExecutionContext`。

```text
用户输入
   |
   v
记录 user Event -> 准备 LlmRequest -> before_llm callbacks -> LlmClient.generate
                                  ^                              |
                                  |                              v
                            ToolResult <--- act(tool calls) <--- LlmResponse
                                  |
                    final answer / pending confirmation / transfer / max_steps
```

每轮会把事件内容扁平化为请求 contents，并把当前工具 schema 放入 `tools`。有工具调用时，Agent 执行工具并再次请求；无工具调用时，普通文本被视为最终答案。`output_type` 模式会注册 `final_answer` 工具，只有该工具成功返回才结束。

`max_steps` 是硬上限。人工确认会让 `run()` 返回 `status="pending"`，此时保存 session 以便恢复并保留待确认状态；transfer 会把同一上下文交给目标 Agent。正常终止时 Agent 才会尝试保存长期 memory 和 session，并清理自己创建的 E2B 环境。
