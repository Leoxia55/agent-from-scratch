# 数据模型参考

导入：`from scratchagent import Message, ToolCall, ToolResult, SummaryMessage, Event`

## 内容模型

```python
Message(role="user", content="你好")
ToolCall(tool_call_id="call_1", name="add", arguments='{"a": 1, "b": 2}')
ToolResult(tool_call_id="call_1", name="add", status="success", content=["3"])
SummaryMessage(content="用户希望得到简洁答案")
```

`Message.role` 只接受 `system`、`user`、`assistant`；`ToolResult.status` 只接受 `success` 或 `error`。`ContentItem` 是四种模型的联合类型。

## `Event`

```python
Event(
    execution_id="exec-1",
    author="calculator",
    content=[Message(role="assistant", content="...")],
)
```

`id` 默认 UUID，`timestamp` 默认当前时间戳；多个 `Event` 在 `ExecutionContext.events` 中按执行顺序追加。事件是 session、上下文摘要和调试输出的共同数据源。

## 执行模型

`ExecutionContext`、`AgentResult`、`PendingToolCall`、`ToolConfirmation` 的字段见[ExecutionContext 概念](../concepts/execution-context.md)和[Agent 参考](agent.md)。这些模型/数据类是运行时契约，不应把任意 JSON 直接当作事件写入。
