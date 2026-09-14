"""orchestration/_transfer.py 单元测试：Agent 转移工具。"""

from __future__ import annotations

import pytest

from scratchagent import Agent, ExecutionContext
from scratchagent.orchestration import create_transfer_tool


class _FakeAgent(Agent):
    def __init__(self, name, description=""):
        super().__init__(model=None, name=name, description=description)


class TestCreateTransferTool:
    def test_empty_agents_raises(self):
        with pytest.raises(ValueError):
            create_transfer_tool([])

    def test_description_from_agent(self):
        a = _FakeAgent("researcher", "Does research")
        t = create_transfer_tool([a])
        assert t.name == "transfer_to_agent"
        assert "researcher" in t.description

    def test_description_fallback(self):
        # 无 description、无 instruction 时回退
        a = _FakeAgent("writer")
        t = create_transfer_tool([a])
        assert "No description" in t.description

    def test_enum_constraint(self):
        a = _FakeAgent("researcher")
        t = create_transfer_tool([a])
        definition = t.tool_definition
        enum = definition["function"]["parameters"]["properties"]["agent_name"][
            "enum"
        ]
        assert enum == ["researcher"]

    async def test_execute_sets_transfer(self):
        a = _FakeAgent("researcher")
        t = create_transfer_tool([a])
        ctx = ExecutionContext()
        result = await t(ctx, agent_name="researcher")
        assert "Transferring" in result
        assert ctx.transfer_to == "researcher"

    async def test_execute_invalid_name(self):
        a = _FakeAgent("researcher")
        t = create_transfer_tool([a])
        ctx = ExecutionContext()
        result = await t(ctx, agent_name="unknown")
        assert "not valid" in result
        assert ctx.transfer_to is None

    async def test_transfer_only_once(self):
        a = _FakeAgent("researcher")
        t = create_transfer_tool([a])
        ctx = ExecutionContext()
        await t(ctx, agent_name="researcher")
        result = await t(ctx, agent_name="researcher")
        assert "already requested" in result
        assert ctx.transfer_to == "researcher"
