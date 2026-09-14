"""sequential-wf-agent 示例：演示多智能体顺序编排

原理
----
SequentialWorkFlow 依次运行多个 Agent，前一个 Agent 产生的上下文
（events）会传递给下一个 Agent。适用于「流水线」式任务，例如：
  研究 → 摘要 → 润色。

第一个 Agent 接收 user_input，后续 Agent 直接基于传递下来的 context 继续工作。

关键 API
--------
  SequentialWorkFlow(agents=[agent_a, agent_b, ...])

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/sequential_wf_agent.py
"""

import asyncio

from scratchagent import Agent, SequentialWorkFlow
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.tools import FunctionTool, search_web


async def sequential_wf_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT, model="gpt-5.5"
        )
    )

    # 第一个 Agent：研究员，负责搜集信息
    researcher = Agent(
        model=openai_client,
        name="researcher",
        tools=[FunctionTool(search_web)],
        instruction="You are a researcher. 搜集并整理给定主题的关键事实。",
    )

    # 第二个 Agent：撰稿人，基于研究员的成果写一段摘要
    writer = Agent(
        model=openai_client,
        name="writer",
        instruction=(
            "You are a writer. 基于前面研究员整理的资料，"
            "写一段不超过 200 字的简洁摘要。"
        ),
    )

    workflow = SequentialWorkFlow(agents=[researcher, writer])

    user_input = "请介绍一下量子计算的基本概念。"
    result = await workflow.run(user_input, verbose=True)
    print(f"\n最终结果是：{result.output}")


if __name__ == "__main__":
    asyncio.run(sequential_wf_agent())
