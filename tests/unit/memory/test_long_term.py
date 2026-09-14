"""memory/_long_term.py 单元测试：任务长期记忆。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from scratchagent import Event, ExecutionContext, Message, ToolCall, ToolResult
from scratchagent.memory import TaskMemory, TaskMemoryManager


class TestTaskMemory:
    def test_fields(self):
        m = TaskMemory(
            task_summary="s",
            approach="a",
            final_answer="ans",
            is_correct=True,
        )
        assert m.error_analysis is None

    def test_to_embedding_text(self):
        m = TaskMemory(
            task_summary="s", approach="a", final_answer="ans", is_correct=True
        )
        assert m.to_embedding_text() == "Task: s"


def _make_manager() -> TaskMemoryManager:
    """构造一个不真正连 ChromaDB 的 manager（mock collection）。"""
    llm = MagicMock()
    manager = TaskMemoryManager.__new__(TaskMemoryManager)
    manager.llm_client = llm
    manager.collection = MagicMock()
    return manager


class TestFormatExecutionHistory:
    def test_formats_types(self):
        mgr = _make_manager()
        ctx = ExecutionContext()
        ctx.events = [
            Event(
                execution_id=ctx.execution_id,
                author="user",
                content=[Message(role="user", content="hi")],
            ),
            Event(
                execution_id=ctx.execution_id,
                author="agent",
                content=[
                    ToolCall(
                        tool_call_id="t1", name="calc", arguments={"x": 1}
                    ),
                    ToolResult(
                        tool_call_id="t1",
                        name="calc",
                        status="success",
                        content=["4"],
                    ),
                ],
            ),
        ]
        text = mgr._format_execution_history(ctx.events)
        assert "[user]" in text
        assert "calc" in text


class TestExtractMemory:
    async def test_success(self):
        mgr = _make_manager()
        memory = TaskMemory(
            task_summary="s", approach="a", final_answer="ans", is_correct=True
        )
        mgr.llm_client.ask = AsyncMock(return_value=memory)
        result = await mgr._extract_memory("history")
        assert result == memory

    async def test_failure_returns_none(self):
        mgr = _make_manager()
        mgr.llm_client.ask = AsyncMock(side_effect=Exception("boom"))
        result = await mgr._extract_memory("history")
        assert result is None


class TestSave:
    async def test_duplicate_skip(self):
        mgr = _make_manager()
        memory = TaskMemory(
            task_summary="s", approach="a", final_answer="ans", is_correct=True
        )
        mgr._extract_memory = AsyncMock(return_value=memory)
        # 直接 mock 去重判断返回 True（重复）
        mgr._is_duplicate = AsyncMock(return_value=True)

        ctx = ExecutionContext()
        result = await mgr.save(ctx)
        assert result is None
        mgr.collection.add.assert_not_called()

    async def test_save_new(self):
        mgr = _make_manager()
        memory = TaskMemory(
            task_summary="s", approach="a", final_answer="ans", is_correct=True
        )
        mgr._extract_memory = AsyncMock(return_value=memory)
        mgr._is_duplicate = AsyncMock(return_value=False)

        ctx = ExecutionContext()
        result = await mgr.save(ctx)
        assert result is not None
        mgr.collection.add.assert_called_once()

    async def test_extract_memory_none_returns_none(self):
        mgr = _make_manager()
        mgr._extract_memory = AsyncMock(return_value=None)
        ctx = ExecutionContext()
        result = await mgr.save(ctx)
        assert result is None
        mgr.collection.add.assert_not_called()


class TestSearch:
    async def test_empty(self):
        mgr = _make_manager()
        mgr.collection.query.return_value = {"metadatas": [[]]}
        assert await mgr.search("q") == []

    async def test_returns_memories(self):
        mgr = _make_manager()
        mgr.collection.query.return_value = {
            "metadatas": [
                [
                    {
                        "task_summary": "s",
                        "approach": "a",
                        "final_answer": "ans",
                        "is_correct": True,
                        "error_analysis": "",
                    }
                ]
            ]
        }
        results = await mgr.search("q")
        assert len(results) == 1
        assert isinstance(results[0], TaskMemory)
