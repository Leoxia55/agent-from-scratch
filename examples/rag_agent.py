"""rag-agent 示例：演示检索增强生成（RAG）

原理
----
在调用 LLM 之前，先从本地知识库检索出与问题最相关的文本片段，注入到
上下文中，从而让模型基于私有资料回答。

本示例流程：
  1. fixed_length_chunking 将知识库文本切分为带重叠的块；
  2. get_embeddings 对每个块生成向量（走 OPENROUTER 的 embedding 模型）；
  3. vector_search 对用户问题做向量检索，取 top-k 相关块；
  4. 将检索结果拼入提示词，交给 Agent 回答。

关键 API
--------
  fixed_length_chunking(text, chunk_size, overlap)
  get_embeddings(texts)
  vector_search(query, chunks, chunk_embeddings, top_k)

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/rag_agent.py
"""

import asyncio

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.tools import search_web
from scratchagent.rag import (
    fixed_length_chunking,
    get_embeddings,
    vector_search,
)

# 本地知识库文本（示例：公司内部制度）
KNOWLEDGE_BASE = """
公司考勤制度：员工工作日标准上班时间为上午 9:00，下班时间为下午 6:00，
中午 12:00 至 13:30 为午休时间。员工每月累计迟到超过 3 次将影响当月全勤奖。

公司请假制度：员工请假需提前一天在 OA 系统提交申请，病假需附医院证明，
年假可随时申请且无需理由。事假超过 3 天需部门主管审批。

公司报销制度：差旅报销需在出差结束后 15 天内提交，需保留发票原件，
住宿标准为一线城市每晚不超过 600 元，其他城市每晚不超过 400 元。
"""


async def rag_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT, model="gpt-5.5"
        )
    )

    # 1. 切分知识库
    chunks = fixed_length_chunking(KNOWLEDGE_BASE, chunk_size=100, overlap=20)
    print(f"[RAG] 知识库切分为 {len(chunks)} 个块")

    # 2. 生成块向量
    chunk_embeddings = get_embeddings(chunks)

    # 3. 对用户问题进行向量检索,这里特别指出到 邯郸，系统首先应该去检索这个城市属于几线城市，然后再结合知识库回答
    user_question = "员工到邯郸出差报销的住宿标准是多少？"
    retrieved = vector_search(user_question, chunks, chunk_embeddings, top_k=2)

    # 4. 将检索结果注入提示词
    context_text = "\n\n".join(r["chunk"] for r in retrieved)
    instruction = (
        "你是公司的制度咨询助手。请只根据下面提供的资料回答问题，"
        "资料中没有的信息请明确说明「资料中未提及」。\n\n"
        f"<参考资料>\n{context_text}\n</参考资料>"
    )

    agent = Agent(
        model=openai_client,
        tools=[search_web],
        instruction=instruction,
    )

    result = await agent.run(user_question)
    print(f"\n[RAG 检索到的片段]\n{context_text}\n")
    print(f"最终结果是：{result.output}")


if __name__ == "__main__":
    asyncio.run(rag_agent())
