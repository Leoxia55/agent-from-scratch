"""orchestration/_sequential.py 单元测试：顺序工作流。"""

from __future__ import annotations

import pytest

from scratchagent import Agent, AgentResult, ExecutionContext, Message
from scratchagent.orchestration import SequentialWorkFlow


def _make_agent(name, output):
    class FakeModel:
        async def generate(self, request):
            from scratchagent.llm import LlmResponse

            return LlmResponse(content=[Message(role="assistant", content=output)])

    return Agent(model=FakeModel(), name=name)


class TestSequentialWorkFlow:
    async def test_empty_agents_raises(self):
        wf = SequentialWorkFlow(agents=[])
        with pytest.raises(ValueError):
            await wf.run("hi")

    async def test_runs_in_sequence(self):
        order = []

        class RecordingAgent(Agent):
            def __init__(self, name, output):
                super().__init__(model=None, name=name)
                self._output = output

            async def run(self, **kwargs):
                order.append(self.name)
                ctx = kwargs.get("context") or ExecutionContext()
                ctx.final_result = self._output
                return AgentResult(
                    output=self._output, context=ctx, status="complete"
                )

        a1 = RecordingAgent("a1", "one")
        a2 = RecordingAgent("a2", "two")
        wf = SequentialWorkFlow(agents=[a1, a2])
        result = await wf.run("hi")
        assert order == ["a1", "a2"]
        assert result.output == "two"

    async def test_context_passed_between_agents(self):
        seen = {}

        class ContextAgent(Agent):
            def __init__(self, name):
                super().__init__(model=None, name=name)

            async def run(self, **kwargs):
                ctx = kwargs.get("context") or ExecutionContext()
                ctx.state.setdefault("count", 0)
                ctx.state["count"] += 1
                return AgentResult(output="ok", context=ctx, status="complete")

        a1 = ContextAgent("a1")
        a2 = ContextAgent("a2")
        wf = SequentialWorkFlow(agents=[a1, a2])
        result = await wf.run("hi")
        assert result.context.state["count"] == 2

    def test_inherits_agent_attributes(self):
        wf = SequentialWorkFlow(agents=[])
        assert wf.name == "sequential_workflow"
