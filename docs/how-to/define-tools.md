# 定义工具

优先使用 `@tool`，让函数类型和默认值自动生成 schema；需要自定义执行逻辑或请求处理时再实现 `BaseTool`。

## 函数工具

```python
from scratchagent import ExecutionContext
from scratchagent.tools import tool


@tool(name="lookup_user", description="按用户编号返回用户摘要")
def lookup_user(user_id: str, context: ExecutionContext) -> str:
    return f"user={user_id}, execution={context.execution_id}"
```

`context` 参数可放在任意位置，会被执行器注入并从 JSON Schema 中排除。同步函数和 async 函数都可以。

## 自定义 schema

```python
from scratchagent.tools import FunctionTool

tool = FunctionTool(
    func=lookup_user,
    tool_definition={
        "type": "function",
        "function": {
            "name": "lookup_user",
            "description": "按用户编号返回用户摘要",
            "parameters": {
                "type": "object",
                "properties": {"user_id": {"type": "string"}},
                "required": ["user_id"],
            },
        },
    },
)
```

## 沙箱工具

`sandbox_executable=True` 的函数会被上传到 E2B 环境执行，不能声明 `context` 参数，也必须以 `Agent(code_execution="e2b")` 使用。避免把密钥、宿主路径或任意网络客户端写进沙箱工具。

## 返回值

工具返回值会被转换为 `ToolResult.content` 中的字符串或字典。异常不会直接冒泡给模型，而是形成 `status="error"` 的工具结果；工具内部仍应做输入校验。

