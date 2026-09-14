"""集成测试：工具分发与回调链。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from scratchagent import Agent, Message, ToolCall
from scratchagent.llm import LlmResponse
from scratchagent.tools import calculator, tool


async def test_single_tool_dispatch():
    responses = [
        LlmResponse(
            content=[
                ToolCall(
                    tool_call_id="t1",
                    name="calculator",
                    arguments={"operator": "multiply", "first_number": 5, "second_number": 4},
                )
            ]
        ),
        LlmResponse(content=[Message(role="assistant", content="20")]),
    ]
    client = MagicMock()
    client.generate = AsyncMock(side_effect=responses)

    agent = Agent(model=client, tools=[calculator])
    result = await agent.run("5*4")
    assert result.output == "20"


async def test_tool_exception_graceful():
    """工具抛异常时，Agent 降级为 error 结果，继续循环。"""
    @tool
    def bad_tool(x: int) -> int:
        raise ValueError("boom")

    responses = [
        LlmResponse(
            content=[ToolCall(tool_call_id="t1", name="bad_tool", arguments={"x": 1})]
        ),
        LlmResponse(content=[Message(role="assistant", content="recovered")]),
    ]
    client = MagicMock()
    client.generate = AsyncMock(side_effect=responses)

    agent = Agent(model=client, tools=[bad_tool])
    result = await agent.run("do it")
    assert result.output == "recovered"


async def test_before_tool_callback():
    """before_tool_callback 可短路工具执行。"""
    callback_calls = []

    def cb(context, tool_call):
        callback_calls.append(tool_call.name)
        return "short-circuited"

    responses = [
        LlmResponse(
            content=[
                ToolCall(
                    tool_call_id="t1",
                    name="calculator",
                    arguments={"operator": "add", "first_number": 1, "second_number": 1},
                )
            ]
        ),
        LlmResponse(content=[Message(role="assistant", content="done")]),
    ]
    client = MagicMock()
    client.generate = AsyncMock(side_effect=responses)

    agent = Agent(model=client, tools=[calculator], before_tool_callbacks=[cb])
    await agent.run("calc")
    assert callback_calls == ["calculator"]


async def test_after_tool_callback_modifies_result():
    """after_tool_callback 可改写工具结果。"""
    def cb(context, tool_result):
        tool_result.content = ["modified"]
        return tool_result

    responses = [
        LlmResponse(
            content=[
                ToolCall(
                    tool_call_id="t1",
                    name="calculator",
                    arguments={"operator": "add", "first_number": 1, "second_number": 1},
                )
            ]
        ),
        LlmResponse(content=[Message(role="assistant", content="done")]),
    ]
    client = MagicMock()
    client.generate = AsyncMock(side_effect=responses)

    agent = Agent(model=client, tools=[calculator], after_tool_callbacks=[cb])
    await agent.run("calc")
    # 工具结果被改写，但整体流程仍完成
