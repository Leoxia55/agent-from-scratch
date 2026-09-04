# 01. 工具 Agent

目标：让 Agent 先调用一个 Python 工具，再根据工具结果回答问题。

## 1. 定义工具

`@tool` 会把函数签名转换为 JSON Schema。没有默认值的参数会进入 `required`；名为 `context` 的参数由框架注入，不会出现在 schema 中。

```python
import asyncio

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.tools import tool


@tool(description="将两个整数相加")
def add(a: int, b: int) -> int:
    return a + b


async def main() -> None:
    config = resolve_model_config(Provider.OPENAI_COMPAT, "gpt-4o-mini")
    client = LlmClient(default_config=config)
    agent = Agent(
        model=client,
        name="calculator",
        instruction="需要计算时调用工具，并解释计算结果。",
        tools=[add],
        max_steps=5,
    )

    result = await agent.run("计算 41 + 1，并告诉我调用了什么。")
    print(result.status)
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
```

## 2. 观察 loop

一次 `run()` 会重复执行 `step()`：准备请求、调用模型、记录响应、执行工具，再把 `ToolResult` 放回上下文。模型输出不再包含工具调用时，普通文本会被识别为最终答案。`max_steps` 是防止无限循环的硬上限。

## 3. 使用执行上下文

```python
from scratchagent import ExecutionContext


@tool(description="读取本次执行编号")
def execution_id(context: ExecutionContext) -> str:
    return context.execution_id
```

上下文还可以保存 `state`、session、memory manager、E2B 环境和 transfer 目标。详见[ExecutionContext](../concepts/execution-context.md)。

## 4. 常见边界

- 工具异常会被包装成 `ToolResult(status="error")`，模型仍会获得错误内容。
- 标记 `sandbox_executable=True` 的工具必须配合 `code_execution="e2b"`。
- 工具描述和参数类型会直接影响模型是否正确调用，先写清楚 schema，再调 prompt。

下一步：[会话与记忆](02-session-and-memory.md)。

