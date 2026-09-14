"""tools/_callbacks.py 单元测试：审批与搜索结果压缩回调。"""

from __future__ import annotations

from scratchagent import Event, ExecutionContext, ToolCall, ToolResult
from scratchagent.tools._callbacks import (
    approval_callback,
    search_compressor,
    _extract_search_query,
)


# ---------------------------------------------------------------- approval_callback
class TestApprovalCallback:
    def test_non_dangerous_tool_returns_none(self):
        ctx = ExecutionContext()
        tc = ToolCall(tool_call_id="t1", name="calculator", arguments={})
        assert approval_callback(ctx, tc) is None

    def test_dangerous_tool_approved(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda *a, **k: "y")
        ctx = ExecutionContext()
        tc = ToolCall(tool_call_id="t1", name="delete_file", arguments={})
        assert approval_callback(ctx, tc) is None

    def test_dangerous_tool_rejected(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda *a, **k: "n")
        ctx = ExecutionContext()
        tc = ToolCall(tool_call_id="t1", name="delete_file", arguments={})
        result = approval_callback(ctx, tc)
        assert result is not None
        assert "denied" in result


# ---------------------------------------------------------------- _extract_search_query
class TestExtractSearchQuery:
    def test_finds_query(self):
        ctx = ExecutionContext()
        tc = ToolCall(tool_call_id="t1", name="search_web", arguments={"query": "hello"})
        ctx.add_event(
            Event(execution_id=ctx.execution_id, author="agent", content=[tc])
        )
        assert _extract_search_query(ctx, "t1") == "hello"

    def test_not_found(self):
        ctx = ExecutionContext()
        assert _extract_search_query(ctx, "missing") == ""

    def test_str_arguments_json(self):
        ctx = ExecutionContext()
        tc = ToolCall(
            tool_call_id="t1", name="search_web", arguments='{"query": "hello"}'
        )
        ctx.add_event(
            Event(execution_id=ctx.execution_id, author="agent", content=[tc])
        )
        assert _extract_search_query(ctx, "t1") == "hello"


# ---------------------------------------------------------------- search_compressor
class TestSearchCompressor:
    def test_non_search_tool_returns_none(self):
        ctx = ExecutionContext()
        tr = ToolResult(
            tool_call_id="t1", name="calculator", status="success", content=["4"]
        )
        assert search_compressor(ctx, tr) is None

    def test_non_success_returns_none(self):
        ctx = ExecutionContext()
        tr = ToolResult(
            tool_call_id="t1", name="search_web", status="error", content=["x"]
        )
        assert search_compressor(ctx, tr) is None

    def test_empty_content_returns_none(self):
        ctx = ExecutionContext()
        tr = ToolResult(tool_call_id="t1", name="search_web", status="success", content=[])
        assert search_compressor(ctx, tr) is None

    def test_no_query_returns_none(self):
        ctx = ExecutionContext()
        tr = ToolResult(
            tool_call_id="t1", name="search_web", status="success", content=["content"]
        )
        assert search_compressor(ctx, tr) is None

    def test_short_web_text_returns_none(self):
        ctx = ExecutionContext()
        tr = ToolResult(
            tool_call_id="t1",
            name="search_web",
            status="success",
            content=[[{"title": "t", "content": "short", "url": "u"}]],
        )
        assert search_compressor(ctx, tr) is None
