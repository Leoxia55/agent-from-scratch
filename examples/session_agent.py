"""session-agent 示例：演示多轮会话持久化

原理
----
通过 InMemorySessionManager 为 Agent 提供会话存储。传入同一个 session_id 时，
Agent 会恢复该会话的历史 events 与 state，从而在多次 run() 之间保持上下文，
实现真正的多轮对话。

注意：InMemorySessionManager 仅在内存中保存，进程退出即丢失；
生产环境可继承 BaseSessionManager 实现数据库/文件持久化。

关键 API
--------
  InMemorySessionManager()
  Agent(session_manager=...)
  agent.run(user_input, session_id=..., user_id=...)

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/session_agent.py
"""

import asyncio

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.memory import InMemorySessionManager


async def session_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT, model="gpt-5.5"
        )
    )

    session_manager = InMemorySessionManager()

    agent = Agent(
        model=openai_client,
        instruction="You are a helpful assistant. 回答要简洁。",
        session_manager=session_manager,
    )

    session_id = "demo-session-001"

    # 第一轮：建立一个上下文（我的名字）
    first_input = "你好，我叫老夏，是一名软件工程师。请记住我。"
    result1 = await agent.run(first_input, session_id=session_id, user_id="user-1")
    print(f"[第一轮] {result1.output}\n")

    # 第二轮：不重复自我介绍，直接追问，验证会话记忆是否生效
    second_input = "你还记得我叫什么、做什么工作吗？"
    result2 = await agent.run(second_input, session_id=session_id, user_id="user-1")
    print(f"[第二轮] {result2.output}")


if __name__ == "__main__":
    asyncio.run(session_agent())
