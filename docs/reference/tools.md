# 工具参考

## `BaseTool`

```python
BaseTool(
    name=None,
    description=None,
    tool_definition=None,
    required_confirmation=False,
    confirmation_message_template=None,
)
```

子类必须实现 `async execute(context, **kwargs)`。`process_llm_request(context, request)` 默认不做任何事，可用于注入记忆或修改请求。`get_confirmation_message(arguments)` 根据模板生成审批提示；模板可用的占位符仅为 `{name}` 和 `{arguments}`。

## `FunctionTool`

```python
FunctionTool(
    func,
    name=None,
    description=None,
    tool_definition=None,
    sandbox_executable=False,
    required_confirmation=False,
    confirmation_message_template="",
)
```

它包装同步或异步函数，自动生成 schema；`sandbox_executable=True` 时可用 `get_source_code()` 上传 E2B，但函数不能有 `context` 参数。

## `@tool`

```python
@tool
def ping(value: str) -> str: ...

@tool(
    name="dangerous_action",
    description="执行外部写入",
    required_confirmation=True,
    confirmation_message="确认执行 {name}，参数：{arguments}？",
)
def dangerous_action(value: str) -> str: ...
```

Agent 初始化时会把裸 callable 转成 `FunctionTool`。当 `output_type` 存在时，Agent 额外注册内部 `final_answer` 工具；开启 E2B 时额外注册三个沙箱工具。
