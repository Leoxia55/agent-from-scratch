"""search-compressor-agent 示例：演示搜索结果压缩

原理
----
当 search_web 返回大量结果时，会占用大量上下文窗口。search_compressor
是一个 after_tool_callback：在 search_web 工具执行后，对结果文本做切块 +
向量化，再用向量检索挑选与原始查询最相关的 top-k 片段，从而压缩结果。

本示例同时演示：
  1. 正常使用 search_web 工具检索；
  2. 挂载 search_compressor 回调，自动压缩过长结果。

关键 API
--------
  from scratchagent.tools import search_compressor, search_web
  Agent(after_tool_callbacks=[search_compressor], ...)

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/search_compressor_agent.py
"""

import asyncio

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.tools import FunctionTool, search_compressor, search_web


async def search_compressor_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT, model="gpt-5.5"
        )
    )

    agent = Agent(
        model=openai_client,
        tools=[FunctionTool(search_web)],
        instruction="You are a helpful assistant. 基于搜索结果回答问题。",
        # 关键：把 search_compressor 挂到工具执行后的回调上
        after_tool_callbacks=[search_compressor],
    )

    user_input = "请搜索「大语言模型 上下文窗口 优化」的相关信息，并总结要点。"
    result = await agent.run(user_input)
    print(f"\n最终结果是：{result.output}")


if __name__ == "__main__":
    asyncio.run(search_compressor_agent())
