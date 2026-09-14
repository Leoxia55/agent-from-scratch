"""memory-agent 示例：演示长期记忆的存储、检索与复用

原理
----
TaskMemoryManager 借助 ChromaDB 存储「解题记录」：每次 run() 结束后，
Agent 会调用 memory_manager.save(context)，用 LLM 把这次解题过程提炼成
结构化记忆（task_summary / approach / final_answer / is_correct /
error_analysis）并向量化入库；下次遇到相似问题时，MemoryTool 会在请求
LLM 前自动检索相关历史经验并注入到 prompt 中，让模型「复用方法论」。

本示例用「信息检索 + 归纳」这类需要调用工具的多步任务来演示：
  1. 第一轮：搜索并总结「量子计算在药物研发中的应用」，
     → 产生真实的检索/归纳解题过程，被 save() 沉淀为记忆；
  2. 显式调用 memory_manager.search() 验证记忆确实已入库；
  3. 第二轮：换一个同构但主题不同的问题，
     → 先手动复现 MemoryTool 的检索，直观展示「注入来源」，
       再真正 run()，模型自动复用第一轮的方法论。

依赖：ChromaDB + OpenAI Embedding（text-embedding-3-small，走 OPENROUTER）
      + Tavily 搜索（TAVILY_API_KEY）。

关键 API
--------
  TaskMemoryManager(llm_client=...)
  memory_manager.search(query, top_k=...)
  Agent(memory_manager=..., ...)   # 自动挂载 MemoryTool

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/memory_agent.py
"""

import asyncio

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.memory import TaskMemoryManager
from scratchagent.tools import FunctionTool, search_web


async def memory_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT, model="gpt-5.5"
        )
    )

    # 长期记忆管理器：内部使用 ChromaDB 存储
    memory_manager = TaskMemoryManager(llm_client=openai_client)

    agent = Agent(
        model=openai_client,
        tools=[FunctionTool(search_web)],
        instruction=(
            "You are a research assistant. "
            "回答问题时先调用 search_web 检索，再归纳总结。"
            "优先参考已有的历史解题经验。"
        ),
        memory_manager=memory_manager,
        max_steps=6,
    )

    # ── 第一轮：产生一次真实的「检索 → 归纳」解题过程 ──
    first_input = "请搜索并总结「量子计算在药物研发中的应用」，给出 3 个要点。"
    print("=" * 60)
    print("[第一轮] 开始求解，run() 结束时会自动保存记忆...")
    result1 = await agent.run(first_input)
    print(f"[第一轮] 结果：{result1.output}")
    print("=" * 60)

    # ── 显式验证：检索刚才保存的记忆 ──
    print("\n[验证] 手动检索记忆库，确认上一轮解题经验已入库：")
    memories = await memory_manager.search("量子计算 药物研发", top_k=3)
    if memories:
        for i, mem in enumerate(memories, 1):
            print(f"  记忆{i}：")
            print(f"    - 问题：{mem.task_summary}")
            print(f"    - 方法：{mem.approach}")
            print(f"    - 是否正确：{mem.is_correct}")
    else:
        print("  （未检索到任何记忆，请检查 embedding 是否走通了 OpenRouter）")
    print("=" * 60)

    # ── 第二轮：同构但主题不同，验证 MemoryTool 自动注入历史经验 ──
    second_input = "请搜索并总结「量子计算在金融风控中的应用」，给出 3 个要点。"
    print("\n[第二轮] 开始求解（MemoryTool 应自动注入上一轮的记忆经验）...")

    # 直观展示：MemoryTool 在第二轮请求 LLM 前，内部正是用本次 query 检索记忆，
    # 命中第一轮的经验后注入到 prompt。这里手动复现一次检索，让「注入来源」可见。
    print("\n  [注入预览] MemoryTool 即将为第二轮注入的历史经验：")
    injected = await memory_manager.search(second_input, top_k=3)
    if injected:
        for i, mem in enumerate(injected, 1):
            print(f"    命中{i}：{mem.task_summary}")
            print(f"            → 复用方法：{mem.approach}")
    else:
        print("    （未命中任何历史经验，MemoryTool 将不注入）")

    result2 = await agent.run(second_input)
    print(f"\n[第二轮] 结果：{result2.output}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(memory_agent())
