"""parallel-wf-agent 示例：演示多智能体并行编排 + 语义综合

原理
----
ParallelWorkFlow 通过 asyncio.gather 同时运行多个 Agent，每个 Agent 独立
处理同一个 user_input，最后把各 Agent 的输出合并为一个结果。

若给 ParallelWorkFlow 传入 synthesizer（一个独立的 LlmClient），则并行
结果不会简单拼接，而是额外调用一次聚合模型，把多视角输出去重、消解
矛盾并提炼成一份连贯的综合结论；未传 synthesizer 时降级为按 Agent 名称
拼接的字符串。

适用于「多视角并行分析」式任务，例如同时从不同角度评审同一份内容。

关键 API
--------
  ParallelWorkFlow(agents=[agent_a, agent_b, ...], synthesizer=llm_client)

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/parallel_wf_agent.py
"""

import asyncio

from scratchagent import Agent, ParallelWorkFlow
from scratchagent.llm import LlmClient, Provider, resolve_model_config


async def parallel_wf_agent() -> None:
    # openai_client = LlmClient(
    #     default_config=resolve_model_config(
    #         provider=Provider.OPENAI_COMPAT, model="gpt-5.5-2026-04-23"
    #     )
    # )
    # 由 LM_studio 提供的Qwen3.8 Openai 接口兼容模型
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.LM_STUDIO, model="qwen/qwen3.8-27b"
        )
    )


    # 三个不同视角的分析 Agent，并行运行
    tech_analyst = Agent(
        model=openai_client,
        name="tech_analyst",
        instruction="You are a technology analyst. 从技术可行性角度分析该主题。",
    )
    market_analyst = Agent(
        model=openai_client,
        name="market_analyst",
        instruction="You are a market analyst. 从市场前景角度分析该主题。",
    )
    risk_analyst = Agent(
        model=openai_client,
        name="risk_analyst",
        instruction="You are a risk analyst. 从潜在风险角度分析该主题。",
    )

    workflow = ParallelWorkFlow(
        agents=[tech_analyst, market_analyst, risk_analyst],
        synthesizer=openai_client,  # 传入聚合模型，启用语义综合
    )

    user_input = "请分析「从第一性原理理解和手写AI智能体框架，不依赖第三方智能体框架，作为教学项目」这一方向。"
    result = await workflow.run(user_input, verbose=True)
    print(f"\n最终结果是：\n{result.output}")


if __name__ == "__main__":
    asyncio.run(parallel_wf_agent())
