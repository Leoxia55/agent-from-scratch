"""transfer-to-agent 示例：演示多智能体路由转接

原理
----
通过 create_transfer_tool 为「路由 Agent」注入一个 transfer_to_agent 工具，
该工具的参数 agent_name 会被约束为子 Agent 名单（enum）。当路由 Agent 判断
当前问题属于某个子 Agent 的专长时，调用该工具设置 context.transfer_to，
Agent.run 检测到后会查找对应子 Agent 并转接上下文继续执行。

关键 API
--------
  create_transfer_tool(target_agents=[...])
  Agent(sub_agents=[...], tools=[transfer_tool, ...])

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/transfer_to_agent.py
"""

import asyncio

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.orchestration import create_transfer_tool


async def transfer_to_agent() -> None:
    # openai_client = LlmClient(
    #     default_config=resolve_model_config(
    #         provider=Provider.OPENAI_COMPAT, model="gpt-5.5-2026-04-23"
    #     )
    # )
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.LM_STUDIO, model="qwen/qwen3.8-27b"
        )
    )
    # 两个专业子 Agent
    math_agent = Agent(
        model=openai_client,
        name="math_agent",
        description="擅长数学计算和逻辑推理。",
        instruction="You are a math expert. 解答数学问题。",
    )
    writer_agent = Agent(
        model=openai_client,
        name="writer_agent",
        description="擅长文字创作和文案撰写。",
        instruction="You are a writing expert. 撰写文案。",
    )

    # 路由 Agent：持有转接工具，负责把问题分发给合适的子 Agent
    transfer_tool = create_transfer_tool([math_agent, writer_agent])

    router = Agent(
        model=openai_client,
        name="router",
        instruction=(
            "You are a router. 判断用户问题属于数学还是写作范畴，"
            "然后调用 transfer_to_agent 把任务转交给对应专家。"
        ),
        tools=[transfer_tool],
        sub_agents=[math_agent, writer_agent],
    )

    user_input = "请写一句关于秋天的优美文案。"
    result = await router.run(user_input, verbose=True)
    print(f"\n最终结果是：{result.output}")


if __name__ == "__main__":
    asyncio.run(transfer_to_agent())
