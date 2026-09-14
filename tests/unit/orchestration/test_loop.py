"""orchestration/_loop.py 单元测试：循环工作流。"""

from __future__ import annotations

import pytest

from scratchagent import Agent, AgentResult, ExecutionContext, Message
from scratchagent.orchestration import LoopWorkFlow


def _make_agent(name, output="result"):
    class FakeModel:
        async def generate(self, request):
            from scratchagent.llm import LlmResponse

            return LlmResponse(content=[Message(role="assistant", content=output)])

    return Agent(model=FakeModel(), name=name)


class TestLoopWorkFlow:
    async def test_empty_agents_raises(self):
        wf = LoopWorkFlow(agents=[])
        with pytest.raises(ValueError):
            await wf.run("hi")

    async def test_runs_until_stop_condition(self):
        calls = []

        class CountingAgent(Agent):
            async def run(self, **kwargs):
                calls.append(1)
                ctx = kwargs.get("context") or ExecutionContext()
                return AgentResult(output="ok", context=ctx, status="complete")

        a = CountingAgent(model=None, name="a")
        wf = LoopWorkFlow(
            agents=[a],
            stop_condition=lambda result, i: i >= 2,
            max_iterations=10,
        )
        result = await wf.run("hi")
        assert result.output == "ok"
        assert len(calls) == 2

    async def test_max_iterations_guard(self):
        calls = []

        class CountingAgent(Agent):
            async def run(self, **kwargs):
                calls.append(1)
                ctx = kwargs.get("context") or ExecutionContext()
                return AgentResult(output="ok", context=ctx, status="complete")

        a = CountingAgent(model=None, name="a")
        wf = LoopWorkFlow(agents=[a], stop_condition=None, max_iterations=3)
        await wf.run("hi")
        assert len(calls) == 3

    def test_inherits_agent_attributes(self):
        wf = LoopWorkFlow(agents=[])
        # super().__init__ 补上了 Agent 属性
        assert wf.name == "loop_workflow"
        assert wf.description == ""
