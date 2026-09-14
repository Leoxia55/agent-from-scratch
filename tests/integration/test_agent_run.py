"""集成测试：Agent.run 完整循环（mock LLM）。"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from scratchagent import Agent, Message, ToolCall
from scratchagent.llm import LlmResponse
from scratchagent.tools import calculator


async def test_run_direct_answer(mock_llm_client):
    agent = Agent(model=mock_llm_client)
    result = await agent.run("hello")
    assert result.status == "complete"
    assert result.output == "ok"


async def test_run_single_tool_call():
    """LLM 先返回 tool_call，再返回最终答案。"""
    from unittest.mock import AsyncMock, MagicMock

    responses = [
        LlmResponse(
            content=[
                ToolCall(
                    tool_call_id="t1",
                    name="calculator",
                    arguments={"operator": "add", "first_number": 2, "second_number": 3},
                )
            ]
        ),
        LlmResponse(content=[Message(role="assistant", content="5")]),
    ]
    client = MagicMock()
    client.generate = AsyncMock(side_effect=responses)

    agent = Agent(model=client, tools=[calculator])
    result = await agent.run("2+3")
    assert result.output == "5"


async def test_run_max_steps_truncation():
    """LLM 一直返回 tool_call，触发 max_steps 截断。"""
    from unittest.mock import AsyncMock, MagicMock

    tool_call_response = LlmResponse(
        content=[
            ToolCall(
                tool_call_id="t1",
                name="calculator",
                arguments={"operator": "add", "first_number": 1, "second_number": 1},
            )
        ]
    )
    client = MagicMock()
    client.generate = AsyncMock(return_value=tool_call_response)

    agent = Agent(model=client, tools=[calculator], max_steps=3)
    result = await agent.run("loop forever")
    # 达到 max_steps 后退出，final_result 为 None
    assert result.status == "complete"
    assert result.output is None


async def test_run_unknown_tool_graceful():
    """未知工具名应被优雅降级，不抛异常。"""
    from unittest.mock import AsyncMock, MagicMock

    responses = [
        LlmResponse(
            content=[
                ToolCall(tool_call_id="t1", name="unknown_tool", arguments={})
            ]
        ),
        LlmResponse(content=[Message(role="assistant", content="done")]),
    ]
    client = MagicMock()
    client.generate = AsyncMock(side_effect=responses)

    agent = Agent(model=client, tools=[calculator])
    result = await agent.run("use unknown tool")
    assert result.output == "done"


async def test_run_requires_model():
    agent = Agent()
    with pytest.raises(ValueError):
        await agent.run("hi")


async def test_run_output_type():
    """output_type 触发 final_answer 工具，结构化输出。"""
    from unittest.mock import AsyncMock, MagicMock
    from pydantic import BaseModel

    class Answer(BaseModel):
        conclusion: str

    responses = [
        LlmResponse(
            content=[
                ToolCall(
                    tool_call_id="t1",
                    name="final_answer",
                    arguments={"output": {"conclusion": "yes"}},
                )
            ]
        )
    ]
    client = MagicMock()
    client.generate = AsyncMock(side_effect=responses)

    agent = Agent(model=client, output_type=Answer)
    result = await agent.run("assess")
    assert isinstance(result.output, Answer)
    assert result.output.conclusion == "yes"


async def test_run_human_in_the_loop():
    """required_confirmation 工具触发 pending 状态。"""
    from unittest.mock import AsyncMock, MagicMock

    from scratchagent.tools import tool

    @tool(required_confirmation=True)
    def publish_report(report: str) -> str:
        return f"published {report}"

    responses = [
        LlmResponse(
            content=[
                ToolCall(
                    tool_call_id="t1",
                    name="publish_report",
                    arguments={"report": "r"},
                )
            ]
        )
    ]
    client = MagicMock()
    client.generate = AsyncMock(side_effect=responses)

    agent = Agent(model=client, tools=[publish_report])
    result = await agent.run("publish")
    assert result.status == "pending"
    assert len(result.pending_tool_calls) == 1
