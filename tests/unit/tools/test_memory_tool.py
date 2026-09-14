"""tools/_memory_tool.py 单元测试：记忆注入工具。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from scratchagent import ExecutionContext, Message
from scratchagent.llm import LlmRequest
from scratchagent.tools import MemoryTool


class TestMemoryTool:
    def test_tool_definition_none(self):
        tool = MemoryTool()
        assert tool.tool_definition is None

    def test_name(self):
        assert MemoryTool().name == "recall_memory"

    async def test_execute_no_manager(self):
        tool = MemoryTool()
        ctx = ExecutionContext()
        assert await tool.execute(ctx, query="q") == ""

    async def test_execute_with_manager(self):
        tool = MemoryTool()
        ctx = ExecutionContext()

        memory = MagicMock()
        memory.is_correct = True
        memory.error_analysis = None
        memory.task_summary = "summary"
        memory.approach = "approach"
        memory.final_answer = "answer"

        ctx.memory_manager = MagicMock()
        ctx.memory_manager.search = AsyncMock(return_value=[memory])

        result = await tool.execute(ctx, query="q")
        assert "summary" in result
        assert "approach" in result

    async def test_execute_empty_results(self):
        tool = MemoryTool()
        ctx = ExecutionContext()
        ctx.memory_manager = MagicMock()
        ctx.memory_manager.search = AsyncMock(return_value=[])
        assert await tool.execute(ctx, query="q") == ""

    async def test_process_llm_request_no_manager(self):
        tool = MemoryTool()
        ctx = ExecutionContext()
        req = LlmRequest(contents=[Message(role="user", content="hi")])
        await tool.process_llm_request(ctx, req)
        assert req.instructions == []

    async def test_process_llm_request_no_user_msg(self):
        tool = MemoryTool()
        ctx = ExecutionContext()
        ctx.memory_manager = MagicMock()
        req = LlmRequest()
        await tool.process_llm_request(ctx, req)
        assert req.instructions == []

    async def test_process_llm_request_injects(self):
        tool = MemoryTool()
        ctx = ExecutionContext()
        memory = MagicMock()
        memory.is_correct = True
        memory.error_analysis = None
        memory.task_summary = "summary"
        memory.approach = "approach"
        memory.final_answer = "answer"
        ctx.memory_manager = MagicMock()
        ctx.memory_manager.search = AsyncMock(return_value=[memory])

        req = LlmRequest(contents=[Message(role="user", content="hi")])
        await tool.process_llm_request(ctx, req)
        assert len(req.instructions) == 1
        assert "<PAST_EXPERIENCES>" in req.instructions[0]
