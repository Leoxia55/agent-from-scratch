"""集成测试：多智能体编排工作流。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from scratchagent import Agent, Message
from scratchagent.llm import LlmResponse
from scratchagent.orchestration import (
    LoopWorkFlow,
    ParallelWorkFlow,
    SequentialWorkFlow,
)


def _make_agent(name, output):
    client = MagicMock()
    client.generate = AsyncMock(
        return_value=LlmResponse(content=[Message(role="assistant", content=output)])
    )
    return Agent(model=client, name=name)


async def test_sequential_workflow():
    a1 = _make_agent("a1", "one")
    a2 = _make_agent("a2", "two")
    a3 = _make_agent("a3", "three")
    wf = SequentialWorkFlow(agents=[a1, a2, a3])
    result = await wf.run("go")
    assert result.output == "three"


async def test_parallel_workflow():
    a1 = _make_agent("a1", "one")
    a2 = _make_agent("a2", "two")
    wf = ParallelWorkFlow(agents=[a1, a2])
    result = await wf.run("go")
    assert "[a1]" in result.output
    assert "[a2]" in result.output


async def test_loop_workflow():
    a1 = _make_agent("a1", "draft")
    calls = []

    class CountingAgent(Agent):
        def __init__(self, name):
            super().__init__(model=None, name=name)

        async def run(self, **kwargs):
            calls.append(1)
            from scratchagent import AgentResult, ExecutionContext

            ctx = kwargs.get("context") or ExecutionContext()
            ctx.final_result = "x"
            return AgentResult(output="x", context=ctx, status="complete")

    agent = CountingAgent("counter")
    wf = LoopWorkFlow(
        agents=[agent],
        stop_condition=lambda result, i: i >= 2,
        max_iterations=10,
    )
    await wf.run("go")
    assert len(calls) == 2


async def test_nested_workflow():
    """workflow 套 workflow。"""
    a1 = _make_agent("a1", "inner")
    inner = SequentialWorkFlow(agents=[a1])
    a2 = _make_agent("a2", "outer")
    outer = SequentialWorkFlow(agents=[inner, a2])
    result = await outer.run("go")
    assert result.output == "outer"
