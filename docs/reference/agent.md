# Agent 参考

导入：`from scratchagent import Agent`

## 构造函数

```python
Agent(
    model,
    tools=None,
    instruction="",
    name="agent",
    max_steps=10,
    description="",
    output_type=None,
    before_tool_callbacks=None,
    after_tool_callbacks=None,
    session_manager=None,
    memory_manager=None,
    before_llm_callbacks=None,
    code_execution=None,
    skills_path=None,
    sub_agents=None,
    disallow_transfer_to_peers=False,
)
```

- `model`：`LlmClient` 实例。
- `tools`：可调用函数或 `BaseTool` 列表。
- `output_type`：Pydantic 模型类型；启用后 Agent 注册 `final_answer` 工具并返回模型实例。
- `code_execution`：当前支持 `None` 或 `"e2b"`。
- `sub_agents`：可被路由的 Agent 列表。

## 方法

`await run(user_input=None, context=None, session_id=None, user_id=None, tool_confirmations=None, verbose=False) -> AgentResult`

创建或复用上下文，执行 loop，处理确认和 transfer。正常终止时保存 session/memory 并清理 Agent 自己创建的 E2B；等待确认时会先保存 session，保留环境以便恢复。

`await step(context, verbose=False) -> AgentResult | None`

执行一轮 LLM 请求和工具调用。遇到 pending confirmation 时返回 `AgentResult(status="pending")`，否则可能继续下一轮。

`await prepare_code_env(context, caller_owns_sandbox=False) -> None`

为指定上下文创建 E2B 环境。`caller_owns_sandbox=True` 时 Agent 不负责清理。

## 结果

`AgentResult.output` 是文本或结构化对象，`context` 是最终执行上下文，`status` 为 `complete`、`pending` 或 `error`，pending 时可查看 `pending_tool_calls`。
