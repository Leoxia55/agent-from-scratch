# 配置人工确认

对删除、发送、付费或写入外部系统的工具，使用 `required_confirmation=True`。

```python
from scratchagent.tools import tool


@tool(
    name="delete_report",
    description="删除指定报告",
    required_confirmation=True,
    confirmation_message="即将执行 {name}，参数：{arguments}。是否继续？",
)
def delete_report(report_id: str) -> str:
    return f"deleted:{report_id}"
```

第一次 `run()` 不会执行工具，而是返回：

```python
result.status == "pending"
result.pending_tool_calls[0].tool_call.tool_call_id
```

应用层展示 `confirmation_message` 后，使用 `ToolConfirmation` 继续：

```python
from scratchagent import ToolConfirmation

pending_id = result.pending_tool_calls[0].tool_call.tool_call_id
approved = await agent.run(
    context=result.context,
    tool_confirmations=[
        ToolConfirmation(tool_call_id=pending_id, approved=True)
    ],
)
```

拒绝时传 `approved=False`；需要修正参数时传 `modified_arguments={...}`。确认只控制该次工具调用，不能替代沙箱、权限、参数校验和审计。

确认消息模板只支持 `{name}` 和 `{arguments}` 两个占位符；工具参数需要从 `arguments` 字典中读取，不能直接使用 `{report_id}` 这类参数名占位符。
