# 工具 Schema

工具有两个独立部分：给模型看的 JSON Schema，以及给执行器调用的 Python 函数。

`FunctionTool` 从签名生成如下结构：

```json
{
  "type": "function",
  "function": {
    "name": "add",
    "description": "将两个整数相加",
    "parameters": {
      "type": "object",
      "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
      "required": ["a", "b"]
    }
  }
}
```

注解支持 `str`、`int`、`float`、`bool`、列表和 Pydantic 模型；有默认值的参数不是 required。`self` 和 `context` 会从 schema 中排除。生成器对参数描述只使用通用的 `Parameter:<name>`，复杂工具应手写 `tool_definition` 或补充函数描述。

模型返回 `ToolCall(name, arguments)`；arguments 可以是 JSON 字符串或字典。Agent 解析后执行 `BaseTool.execute(context, **kwargs)`，结果统一记录成 `ToolResult`。schema 是模型建议，不是安全边界：执行器仍需做类型、范围、权限和资源校验。

