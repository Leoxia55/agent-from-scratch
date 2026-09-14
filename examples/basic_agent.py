"""scratchagent 简单智能体示例"""

import asyncio

from scratchagent import Agent
from scratchagent.llm import (
    LlmClient,
    Provider,
    resolve_model_config,
)
from scratchagent.tools import (
    FunctionTool,
    calculator,
    search_web,
)


async def basic_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT, model="gpt-5.5"
        )
    )

    user_input = (
        "给出一个南太行山3天自驾游计划，从邯郸出发，回到邯郸。"
    )

    agent = Agent(
        model=openai_client,
        tools=[FunctionTool(calculator), FunctionTool(search_web)],
        instruction="You are a helpful assistant",
    )

    result = await agent.run(user_input)
    print(f"最终结果是：{result.output}")


if __name__ == "__main__":
    asyncio.run(basic_agent())
