"""金标测试：人工挑选的端到端风格用例（mock LLM 决策）。

这些 case 对应 README 中的核心教学场景，测试逻辑上有意义的行为闭环。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from scratchagent import Agent, Message, ToolCall
from scratchagent.llm import LlmResponse
from scratchagent.tools import calculator


async def test_golden_calculator():
    """计算器金标：25 * 4 = 100。"""
    responses = [
        LlmResponse(
            content=[
                ToolCall(
                    tool_call_id="t1",
                    name="calculator",
                    arguments={"operator": "multiply", "first_number": 25, "second_number": 4},
                )
            ]
        ),
        LlmResponse(content=[Message(role="assistant", content="100")]),
    ]
    client = MagicMock()
    client.generate = AsyncMock(side_effect=responses)

    agent = Agent(model=client, tools=[calculator])
    result = await agent.run("What is 25 times 4?")
    assert result.output == "100"


async def test_golden_structured_output():
    """结构化输出金标：output_type 校验。"""
    from pydantic import BaseModel

    class Answer(BaseModel):
        answer: int
        unit: str

    responses = [
        LlmResponse(
            content=[
                ToolCall(
                    tool_call_id="t1",
                    name="final_answer",
                    arguments={"output": {"answer": 100, "unit": "cm"}},
                )
            ]
        )
    ]
    client = MagicMock()
    client.generate = AsyncMock(side_effect=responses)

    agent = Agent(model=client, output_type=Answer)
    result = await agent.run("how long?")
    assert result.output.answer == 100
    assert result.output.unit == "cm"


async def test_golden_transfer():
    """多智能体转移金标：router 转移到子 agent。"""
    from scratchagent.orchestration import create_transfer_tool

    # 目标 agent：直接返回答案
    target_client = MagicMock()
    target_client.generate = AsyncMock(
        return_value=LlmResponse(content=[Message(role="assistant", content="from writer")])
    )
    writer = Agent(model=target_client, name="writer", description="Writes text")

    # router：先发起 transfer
    transfer_tool = create_transfer_tool([writer])
    router_client = MagicMock()
    router_client.generate = AsyncMock(
        return_value=LlmResponse(
            content=[
                ToolCall(
                    tool_call_id="t1",
                    name="transfer_to_agent",
                    arguments={"agent_name": "writer"},
                )
            ]
        )
    )
    router = Agent(
        model=router_client,
        name="router",
        tools=[transfer_tool],
        sub_agents=[writer],
    )

    result = await router.run("write something")
    assert result.output == "from writer"
