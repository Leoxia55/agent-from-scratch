"""orchestration/_parallel.py 单元测试：并行工作流。"""

from __future__ import annotations

import pytest

from scratchagent import Agent, AgentResult, ExecutionContext, Message
from scratchagent.orchestration import ParallelWorkFlow


class _FakeAgent(Agent):
    def __init__(self, name, output):
        super().__init__(model=None, name=name)
        self._output = output

    async def run(self, user_input=None, context=None, **kwargs):
        ctx = context or ExecutionContext()
        ctx.final_result = self._output
        return AgentResult(output=self._output, context=ctx, status="complete")


class TestParallelWorkFlow:
    async def test_empty_agents_raises(self):
        wf = ParallelWorkFlow(agents=[])
        with pytest.raises(ValueError):
            await wf.run("hi")

    async def test_combines_outputs(self):
        a1 = _FakeAgent("a1", "one")
        a2 = _FakeAgent("a2", "two")
        wf = ParallelWorkFlow(agents=[a1, a2])
        result = await wf.run("hi")
        assert "[a1]" in result.output
        assert "one" in result.output
        assert "[a2]" in result.output
        assert "two" in result.output

    def test_inherits_agent_attributes(self):
        wf = ParallelWorkFlow(agents=[])
        assert wf.name == "parallel_workflow"
