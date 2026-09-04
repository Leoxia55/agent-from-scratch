# 02. 会话与记忆

本章区分两类状态：session 保存一次用户会话的事件和短期 state；`TaskMemoryManager` 把已完成任务提炼后存入 ChromaDB，供未来任务检索。

## 1. 复用会话

```python
import asyncio

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.memory import InMemorySessionManager


async def main() -> None:
    config = resolve_model_config(Provider.OPENAI_COMPAT, "gpt-4o-mini")
    client = LlmClient(default_config=config)
    sessions = InMemorySessionManager()
    agent = Agent(
        model=client,
        instruction="记住当前对话中的用户偏好。",
        session_manager=sessions,
    )

    first = await agent.run("我喜欢简洁的 Python 示例。", session_id="demo")
    second = await agent.run("我喜欢什么风格的示例？", session_id="demo")
    print(first.status, second.output)


if __name__ == "__main__":
    asyncio.run(main())
```

`Agent.run()` 会从 manager 获取或创建 `Session`，把 session 的 `events` 和 `state` 复制到 `ExecutionContext`，结束时再保存。`InMemorySessionManager` 只适合开发和测试，进程重启后数据会消失。

## 2. 开启长期任务记忆

```python
from scratchagent.memory import TaskMemoryManager

memory = TaskMemoryManager(llm_client=client)
agent = Agent(model=client, memory_manager=memory)
```

每次成功运行后，管理器会让 LLM 提炼 `TaskMemory`，对 ChromaDB 做相似度查询和重复判断，必要时保存新记录。设置 `collection_name` 可隔离不同应用。

## 3. 主动搜索记忆

```python
past = await memory.search("如何生成简洁的 Python 示例？", top_k=3)
for item in past:
    print(item.task_summary, item.final_answer)
```

MemoryTool 会在请求准备阶段自动把相关记忆加入 prompt；只有配置 `memory_manager` 且没有同名工具时才会自动注册。

下一步：[上下文优化](03-context-optimization.md)。

