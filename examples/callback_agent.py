"""callback-agent 示例：演示工具调用回调拦截

原理
----
Agent 在「工具调用前」和「工具调用后」各提供一组回调钩子：
  - before_tool_callbacks：在工具真正执行前触发，返回非 None 会跳过该工具的执行；
  - after_tool_callbacks：在工具执行后触发，可改写（返回新的 ToolResult）或观察结果。

回调签名为 callable(context, tool_call) / callable(context, tool_result)，
支持同步函数和 async 函数。

关键 API
--------
  Agent(before_tool_callbacks=[...], after_tool_callbacks=[...])

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/callback_agent.py
"""

import asyncio

from scratchagent import Agent
from scratchagent.context import ExecutionContext
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.tools import FunctionTool, calculator, search_web
from scratchagent.types import ToolCall, ToolResult


def before_tool_log(context: ExecutionContext, tool_call: ToolCall) -> None:
    """工具执行前：记录即将调用的工具与参数。"""
    print(f"[before_tool] 即将调用工具 -> {tool_call.name}")
    print(f"              参数 -> {tool_call.arguments}")
    return None  # 返回 None 表示不拦截，继续正常执行


def after_tool_log(context: ExecutionContext, tool_result: ToolResult) -> None:
    """工具执行后：记录结果摘要。"""
    preview = (
        str(tool_result.content[0])[:80] if tool_result.content else "<空>"
    )
    print(
        f"[after_tool] 工具 {tool_result.name} 执行完成 "
        f"({tool_result.status}) -> {preview}..."
    )
    return None  # 返回 None 表示不改写结果


async def callback_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT,
            model="gpt-5.5"
        )
    )

    agent = Agent(
        model=openai_client,
        tools=[FunctionTool(calculator), FunctionTool(search_web)],
        instruction="You are a helpful assistant",
        before_tool_callbacks=[before_tool_log],
        after_tool_callbacks=[after_tool_log],
    )

    user_input = """请分别计算 123456 * 789、98765 / 13、45678 + 9876 三个算式的结果，并求和；
    回答任何计算问题时，必须调用 calculator 工具，不要心算。并用一句话告诉我答案。"""
    
    result = await agent.run(user_input)
    print(f"\n最终结果是：{result.output}")


if __name__ == "__main__":
    asyncio.run(callback_agent())
