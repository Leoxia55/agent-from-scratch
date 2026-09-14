"""agent.py 单元测试：Agent 构造与核心行为。"""

from __future__ import annotations

import pytest

from scratchagent import Agent
from scratchagent.tools import FunctionTool, MemoryTool, calculator


def _plain_fn(x: int) -> int:
    """Double x."""
    return x * 2


class TestAgentInit:
    def test_init_minimal(self, mock_llm_client):
        a = Agent(model=mock_llm_client)
        assert a.name == "agent"
        assert a.max_steps == 10
        assert a.instruction == ""
        assert a.description == ""

    def test_init_all_kwargs(self, mock_llm_client):
        a = Agent(
            model=mock_llm_client,
            name="my_agent",
            instruction="be nice",
            max_steps=5,
            description="a test agent",
        )
        assert a.name == "my_agent"
        assert a.instruction == "be nice"
        assert a.max_steps == 5
        assert a.description == "a test agent"

    def test_model_optional(self):
        a = Agent()
        assert a.model is None

    def test_callbacks_default_empty(self, mock_llm_client):
        a = Agent(model=mock_llm_client)
        assert a.before_tool_callbacks == []
        assert a.after_tool_callbacks == []
        assert a.before_llm_callbacks == []

    def test_skill_path_stored(self, mock_llm_client):
        a = Agent(model=mock_llm_client, skills_path="/tmp/skills")
        assert a.skills_path == "/tmp/skills"


class TestSetupTools:
    def test_wraps_callables(self, mock_llm_client):
        a = Agent(model=mock_llm_client, tools=[_plain_fn])
        assert len(a.tools) == 1
        assert isinstance(a.tools[0], FunctionTool)
        assert a.tools[0].name == "_plain_fn"

    def test_rejects_invalid_type(self, mock_llm_client):
        with pytest.raises(TypeError):
            Agent(model=mock_llm_client, tools=[123])

    def test_accepts_base_tool(self, mock_llm_client):
        ft = FunctionTool(_plain_fn)
        a = Agent(model=mock_llm_client, tools=[ft])
        assert a.tools[0] is ft

    def test_output_type_adds_final_answer(self, mock_llm_client):
        from pydantic import BaseModel

        class Answer(BaseModel):
            conclusion: str

        a = Agent(model=mock_llm_client, output_type=Answer)
        names = [t.name for t in a.tools]
        assert "final_answer" in names
        assert a.output_tool_name == "final_answer"

    def test_sandbox_executable_without_code_execution(self, mock_llm_client):
        @FunctionTool
        def sandbox_tool(x: int) -> int:
            return x

        sandbox_tool = FunctionTool(_plain_fn, sandbox_executable=True)
        with pytest.raises(ValueError):
            Agent(model=mock_llm_client, tools=[sandbox_tool])

    def test_memory_manager_dedupes(self, mock_llm_client):
        # 同时传 memory_manager + MemoryTool，应只保留 1 个 recall_memory
        from unittest.mock import MagicMock

        mm = MagicMock()
        a = Agent(
            model=mock_llm_client,
            memory_manager=mm,
            tools=[MemoryTool()],
        )
        recall_count = sum(1 for t in a.tools if t.name == "recall_memory")
        assert recall_count == 1

    def test_memory_manager_adds_tool(self, mock_llm_client):
        from unittest.mock import MagicMock

        mm = MagicMock()
        a = Agent(model=mock_llm_client, memory_manager=mm)
        assert any(t.name == "recall_memory" for t in a.tools)


class TestSubAgents:
    def test_duplicate_name_raises(self, mock_llm_client):
        sub1 = Agent(model=mock_llm_client, name="dup")
        sub2 = Agent(model=mock_llm_client, name="dup")
        with pytest.raises(ValueError):
            Agent(model=mock_llm_client, sub_agents=[sub1, sub2])

    def test_set_parent(self, mock_llm_client):
        sub = Agent(model=mock_llm_client, name="sub")
        a = Agent(model=mock_llm_client, sub_agents=[sub])
        assert sub.parent is a

    def test_has_parent_raises(self, mock_llm_client):
        parent = Agent(model=mock_llm_client, name="p")
        sub = Agent(model=mock_llm_client, name="sub")
        sub.parent = parent
        with pytest.raises(ValueError):
            Agent(model=mock_llm_client, sub_agents=[sub])


class TestAgentLookup:
    def test_find_agent_by_name(self, mock_llm_client):
        sub = Agent(model=mock_llm_client, name="sub")
        a = Agent(model=mock_llm_client, name="root", sub_agents=[sub])
        assert a._find_agent("sub") is sub
        assert a._find_agent("root") is a
        assert a._find_agent("missing") is None

    def test_get_transfer_targets(self, mock_llm_client):
        child = Agent(model=mock_llm_client, name="child")
        root = Agent(model=mock_llm_client, name="root", sub_agents=[child])
        targets = child._get_transfer_targets()
        # child 的 targets 包含 parent (root)，无 siblings
        assert root in targets
