# 配置 Sandbox 和调试

## E2B 配置

```dotenv
E2B_API_KEY=...
E2B_TEMPLATE_ID=your-template
```

```python
agent = Agent(model=client, code_execution="e2b")
```

也可以让调用方持有沙箱：

```python
context = ExecutionContext()
await agent.prepare_code_env(context, caller_owns_sandbox=True)
result = await agent.run("执行检查", context=context)
```

默认超时为 300 秒；`create_e2b_sandbox(timeout=...)` 要求正数。调用方拥有环境时负责最终 `close_e2b_sandbox(context.code_env)`。

## 调试 loop

```python
result = await agent.run("...", verbose=True)
print(result.status, result.context.current_step)
for event in result.context.events:
    print(event.author, event.content)
```

检查顺序：先看 `LlmResponse.error_message`，再看 `ToolResult.status`，最后确认 `max_steps` 是否耗尽。模型请求不接受公开的 `provider` 参数；切换 provider 应在构造 `LlmClient` 时传入新的 `ModelConfig`。

避免打印 API key、完整上传文件和敏感 session。并行工作流的事件写入可能交错，调试时优先使用顺序工作流。

